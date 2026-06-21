#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wheel_conflict_reconciliation_nursery_rhyme.py
=========================================================================

A standalone story world for a tiny nursery-rhyme-style domain:
two small children share a little rolling toy, a bad wheel causes a quarrel,
and a calm grown-up helps them make peace by fixing the real problem.

The world is intentionally narrow and constraint-checked:
different rolling toys can have different wheel troubles, and only the
matching repair counts as a reasonable fix. The conflict is grounded in the
simulated state: a wheel problem makes the toy jerk, spill, or stop; that
jolt raises frustration and blame; the repair lowers the trouble; apology and
sharing then become plausible.

Run it
------
    python storyworlds/worlds/gpt-5.4/wheel_conflict_reconciliation_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/wheel_conflict_reconciliation_nursery_rhyme.py --vehicle wagon --problem pebble_jam --fix pluck_pebble
    python storyworlds/worlds/gpt-5.4/wheel_conflict_reconciliation_nursery_rhyme.py --problem dry_axle --fix tighten_nut
    python storyworlds/worlds/gpt-5.4/wheel_conflict_reconciliation_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wheel_conflict_reconciliation_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/wheel_conflict_reconciliation_nursery_rhyme.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives one level deeper than most worlds:
# storyworlds/worlds/gpt-5.4/<this_file>.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    cargo: str
    ride_verb: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    symptom: str
    clue: str
    cause_line: str
    stop_line: str
    risk_line: str
    child_fix_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    matches: set[str] = field(default_factory=set)
    sense: int = 2
    do_line: str = ""
    result_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_jolt_from_bad_wheel(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.get("wheel")
    toy = world.get("toy")
    if wheel.meters["trouble"] < THRESHOLD:
        return out
    if toy.meters["rolling"] < THRESHOLD:
        return out
    sig = ("jolt", int(wheel.meters["trouble"]), int(toy.meters["rolling"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.meters["jolted"] += 1
    toy.meters["spilled"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
    out.append("__jolt__")
    return out


def _r_conflict_from_jolt(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    if toy.meters["jolted"] < THRESHOLD:
        return out
    a, b = world.get("leader"), world.get("partner")
    sig = ("blame",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["frustration"] += 1
    b.memes["frustration"] += 1
    a.memes["blame"] += 1
    b.memes["blame"] += 1
    out.append("__conflict__")
    return out


def _r_relief_after_fix(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.get("wheel")
    if wheel.meters["trouble"] >= THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="jolt_from_bad_wheel", tag="physical", apply=_r_jolt_from_bad_wheel),
    Rule(name="conflict_from_jolt", tag="social", apply=_r_conflict_from_jolt),
    Rule(name="relief_after_fix", tag="emotional", apply=_r_relief_after_fix),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def compatible_fix(problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.matches and fix.sense >= SENSE_MIN


def sensible_fixes() -> list[Fix]:
    return [fx for fx in FIXES.values() if fx.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for vehicle_id in VEHICLES:
        for problem_id, problem in PROBLEMS.items():
            for fix_id, fix in FIXES.items():
                if compatible_fix(problem, fix):
                    combos.append((vehicle_id, problem_id, fix_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    toy = sim.get("toy")
    toy.meters["rolling"] += 1
    propagate(sim, narrate=False)
    return {
        "jolted": sim.get("toy").meters["jolted"] >= THRESHOLD,
        "spilled": sim.get("toy").meters["spilled"] >= THRESHOLD,
        "frustration": sum(k.memes["frustration"] for k in sim.kids()),
    }


def introduce(world: World, a: Entity, b: Entity, vehicle: Vehicle) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} had {vehicle.phrase}. Round went the wheel, "
        f"and round their song went too."
    )
    world.say(
        f'"Roll, little {vehicle.label}, roll," sang {a.id}. '
        f'"Past the gate and by the tree!"'
    )


def load_toy(world: World, a: Entity, b: Entity, vehicle: Vehicle) -> None:
    toy = world.get("toy")
    toy.meters["loaded"] += 1
    world.say(
        f"They tucked in {vehicle.cargo}, and {b.id} clapped in time. "
        f"The morning felt light as a spoonful of dew."
    )


def hint_problem(world: World, problem: Problem) -> None:
    wheel = world.get("wheel")
    wheel.meters["trouble"] += 1
    wheel.meters["squeak"] += 1
    world.say(
        f"But one small wheel did not feel merry. {problem.symptom}."
    )
    world.say(problem.clue)


def roll_and_jolt(world: World, vehicle: Vehicle, problem: Problem) -> None:
    toy = world.get("toy")
    toy.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Off they went with the {vehicle.label}, but {problem.stop_line}"
    )
    if toy.meters["spilled"] >= THRESHOLD:
        world.say(problem.risk_line)


def quarrel(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f'"You pulled too fast!" cried {b.id}. '
        f'"No, you pushed too hard!" said {a.id}.'
    )
    world.say(
        "Their brows grew scrunched, their voices grew tight, and the game lost its bounce."
    )


def adult_enters(world: World, helper: Entity) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.label_word.capitalize()} heard the fuss and came with quiet steps."
    )
    world.say(
        f'"Hush now, little hearts," {helper.pronoun()} said. '
        f'"Let us look before we scold."'
    )


def inspect(world: World, helper: Entity, problem: Problem) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_jolt"] = pred["jolted"]
    world.facts["predicted_spill"] = pred["spilled"]
    world.say(
        f"{helper.label_word.capitalize()} knelt beside the wheel and peeped close. "
        f"{problem.cause_line}"
    )
    if pred["spilled"]:
        world.say(
            "It was not unkind hands that made the trouble. It was the bad wheel all along."
        )


def fix_wheel(world: World, helper: Entity, fix: Fix) -> None:
    wheel = world.get("wheel")
    wheel.meters["trouble"] = 0.0
    wheel.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.label_word} {fix.do_line}."
    )
    world.say(fix.result_line)


def reconcile(world: World, a: Entity, b: Entity) -> None:
    a.memes["blame"] = 0.0
    b.memes["blame"] = 0.0
    a.memes["frustration"] = 0.0
    b.memes["frustration"] = 0.0
    a.memes["love"] += 1
    b.memes["love"] += 1
    a.memes["apology"] += 1
    b.memes["apology"] += 1
    world.say(
        f'{a.id} looked at {b.id} and whispered, "I am sorry for my sharp words."'
    )
    world.say(
        f'"I am sorry too," said {b.id}, and their hands found each other again.'
    )


def shared_ending(world: World, a: Entity, b: Entity, vehicle: Vehicle) -> None:
    toy = world.get("toy")
    toy.meters["rolling"] += 1
    world.say(
        f"Once more they rolled the {vehicle.label}, and this time the wheel hummed sweet and true."
    )
    world.say(
        f"Together they {vehicle.ride_verb}, and {vehicle.ending_image}."
    )


def tell(
    vehicle: Vehicle,
    problem: Problem,
    fix: Fix,
    leader_name: str = "Mina",
    leader_gender: str = "girl",
    partner_name: str = "Pip",
    partner_gender: str = "boy",
    helper_type: str = "mother",
) -> World:
    world = World()
    a = world.add(Entity(id="leader", kind="character", type=leader_gender, label=leader_name, role="leader"))
    b = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, role="partner"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    toy = world.add(Entity(id="toy", type="toy", label=vehicle.label, phrase=vehicle.phrase, tags=set(vehicle.tags)))
    wheel = world.add(Entity(id="wheel", type="wheel", label="wheel", phrase="one little wheel", tags={"wheel"}))

    introduce(world, a, b, vehicle)
    load_toy(world, a, b, vehicle)

    world.para()
    hint_problem(world, problem)
    roll_and_jolt(world, vehicle, problem)
    quarrel(world, a, b)

    world.para()
    adult_enters(world, helper)
    inspect(world, helper, problem)
    fix_wheel(world, helper, fix)

    world.para()
    reconcile(world, a, b)
    shared_ending(world, a, b, vehicle)

    world.facts.update(
        leader=a,
        partner=b,
        helper=helper,
        vehicle=vehicle,
        problem=problem,
        fix=fix,
        toy=toy,
        wheel=wheel,
        conflict=True,
        reconciled=a.memes["apology"] >= THRESHOLD and b.memes["apology"] >= THRESHOLD,
        repaired=wheel.meters["fixed"] >= THRESHOLD,
    )
    return world


VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a red little wagon with a painted side",
        cargo="three yellow pears and a cloth doll",
        ride_verb="rolled in a gentle ring around the yard",
        ending_image="the pears stayed snug and the doll bobbed like a queen",
        tags={"wagon", "wheel"},
    ),
    "barrow": Vehicle(
        id="barrow",
        label="barrow",
        phrase="a small garden barrow bright as an apple",
        cargo="soft bean pods and one striped mitten",
        ride_verb="pushed along the path in twos and twirls",
        ending_image="the bean pods did not tumble and the striped mitten waved",
        tags={"barrow", "wheel"},
    ),
    "cart": Vehicle(
        id="cart",
        label="cart",
        phrase="a wooden toy cart with blue sides",
        cargo="round buns of mud and a tin cup",
        ride_verb="trundled by the fence with matching feet",
        ending_image="the tin cup chimed and the mud buns sat neat as moons",
        tags={"cart", "wheel"},
    ),
}

PROBLEMS = {
    "pebble_jam": Problem(
        id="pebble_jam",
        label="a pebble jam",
        symptom="A click-clack pebble had wedged by the wheel",
        clue="It made the rim hop and the wagon nip to one side",
        cause_line="A tiny pebble was pinched beside the wheel, stopping the smooth turn.",
        stop_line="the wheel gave a jump, a bump, and a stubborn little stop",
        risk_line="The load tipped crooked, and one of the bright things nearly spilled out.",
        child_fix_need="take the pebble out",
        tags={"pebble", "wheel"},
    ),
    "loose_nut": Problem(
        id="loose_nut",
        label="a loose nut",
        symptom="The wheel waggled with a shaky wobble",
        clue="Each turn made a tick-tick rattle under the axle",
        cause_line="The little nut on the wheel had worked itself loose and let the wheel wobble.",
        stop_line="the wheel wobbled sideways and made the toy shiver",
        risk_line="The cargo slid and bumped because the toy could not roll straight.",
        child_fix_need="tighten the little nut",
        tags={"nut", "wheel"},
    ),
    "dry_axle": Problem(
        id="dry_axle",
        label="a dry axle",
        symptom="The wheel sang a dry squeak instead of a happy hum",
        clue="The axle sounded thirsty, as if it needed a drop of help",
        cause_line="The axle had gone dry, so the wheel scraped instead of spinning easily.",
        stop_line="the wheel squealed and dragged as though it were tired",
        risk_line="The toy slowed to a sulk, and their pulling turned into tugging.",
        child_fix_need="add a drop of oil",
        tags={"axle", "wheel"},
    ),
}

FIXES = {
    "pluck_pebble": Fix(
        id="pluck_pebble",
        label="pluck out the pebble",
        matches={"pebble_jam"},
        sense=3,
        do_line="pinched the tiny pebble free with careful fingers",
        result_line="Out popped the pebble, and the wheel sat round and ready again.",
        qa_line="took the pebble out of the wheel",
        tags={"pebble", "repair"},
    ),
    "tighten_nut": Fix(
        id="tighten_nut",
        label="tighten the nut",
        matches={"loose_nut"},
        sense=3,
        do_line="turned the little nut snug with a small key",
        result_line="The wobble settled down, and the wheel held itself straight.",
        qa_line="tightened the loose nut on the wheel",
        tags={"nut", "repair"},
    ),
    "oil_axle": Fix(
        id="oil_axle",
        label="oil the axle",
        matches={"dry_axle"},
        sense=3,
        do_line="added one shiny drop of oil to the axle",
        result_line="The dry squeak faded, and the wheel spun with a soft purr.",
        qa_line="put a drop of oil on the dry axle",
        tags={"axle", "repair"},
    ),
    "tie_ribbon": Fix(
        id="tie_ribbon",
        label="tie on a ribbon",
        matches=set(),
        sense=1,
        do_line="tied on a ribbon",
        result_line="The ribbon looked pretty, but it did not mend a wheel at all.",
        qa_line="tied a ribbon on the toy",
        tags={"ribbon"},
    ),
}


@dataclass
class StoryParams:
    vehicle: str
    problem: str
    fix: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    helper: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Tilly", "Lulu", "Nora", "Elsie", "Poppy", "Daisy", "Millie"]
BOY_NAMES = ["Pip", "Toby", "Bram", "Ned", "Ollie", "Kit", "Rory", "Benji"]


KNOWLEDGE = {
    "wheel": [
        (
            "What does a wheel do?",
            "A wheel helps a cart or wagon roll smoothly along the ground. When the wheel turns well, pushing feels easy."
        )
    ],
    "pebble": [
        (
            "Why can a pebble stop a wheel?",
            "A small pebble can get stuck near a wheel and block its turning. Even a tiny hard thing can make a big bump."
        )
    ],
    "nut": [
        (
            "What happens when a wheel is loose?",
            "A loose wheel can wobble and shake from side to side. That makes a toy roll badly and can tip what it is carrying."
        )
    ],
    "axle": [
        (
            "What is an axle?",
            "An axle is the rod a wheel turns around. If it is dry, the wheel can squeak and drag."
        )
    ],
    "repair": [
        (
            "Why is it smart to look for the real problem before blaming someone?",
            "Looking first helps you find what truly went wrong. Then you can fix the cause instead of hurting someone's feelings."
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you are sorry for something unkind or hurtful. It helps people begin to mend their feelings."
        )
    ],
    "sharing": [
        (
            "How do children make peace after a quarrel?",
            "They calm down, tell the truth, say sorry, and try again kindly. Doing something together can help the good feeling come back."
        )
    ],
}
KNOWLEDGE_ORDER = ["wheel", "pebble", "nut", "axle", "repair", "apology", "sharing"]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two little girls"
    if a.type == "boy" and b.type == "boy":
        return "two little boys"
    return "two little children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, vehicle, problem = f["leader"], f["partner"], f["vehicle"], f["problem"]
    return [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "wheel".',
        f"Tell a gentle story where {a.label} and {b.label} quarrel because a {vehicle.label} goes wrong, then make peace after the real trouble is found.",
        f"Write a rhyming-feeling story with conflict and reconciliation, where {problem.label} in a little {vehicle.label} causes sharp words before a calm grown-up helps."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["leader"], f["partner"]
    helper = f["helper"]
    vehicle, problem, fix = f["vehicle"], f["problem"], f["fix"]
    hw = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.label} and {b.label}, and their {hw} who helped them. They were trying to roll a little {vehicle.label} together."
        ),
        (
            f"Why did {a.label} and {b.label} begin to argue?",
            f"They argued when the {vehicle.label} jerked and would not roll properly. The bad wheel made them think the other child had caused the trouble."
        ),
        (
            "What was really wrong?",
            f"The real problem was {problem.label}. The wheel itself was making the toy bump, wobble, or drag."
        ),
        (
            f"How did the {hw} help?",
            f"{hw.capitalize()} did not pick a side first. {helper.pronoun().capitalize()} looked closely at the wheel, found the true cause, and {fix.qa_line}."
        ),
        (
            "How did the children make peace?",
            f"They each said they were sorry for their sharp words. Then they held hands again and rolled the toy together, which showed the quarrel was over."
        ),
    ]
    if f.get("repaired"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with the {vehicle.label} rolling smoothly again. The children were no longer blaming each other, and the happy game came back."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"wheel", "repair", "apology", "sharing"} | set(f["problem"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        vehicle="wagon",
        problem="pebble_jam",
        fix="pluck_pebble",
        leader_name="Mina",
        leader_gender="girl",
        partner_name="Pip",
        partner_gender="boy",
        helper="mother",
    ),
    StoryParams(
        vehicle="barrow",
        problem="loose_nut",
        fix="tighten_nut",
        leader_name="Tilly",
        leader_gender="girl",
        partner_name="Lulu",
        partner_gender="girl",
        helper="grandmother",
    ),
    StoryParams(
        vehicle="cart",
        problem="dry_axle",
        fix="oil_axle",
        leader_name="Toby",
        leader_gender="boy",
        partner_name="Nora",
        partner_gender="girl",
        helper="father",
    ),
]


def explain_rejection(problem: Problem, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(No story: '{fix.id}' is known here, but it is not a sensible wheel repair "
            f"(sense={fix.sense} < {SENSE_MIN}). Pick a real fix that matches {problem.label}.)"
        )
    return (
        f"(No story: {fix.label} does not solve {problem.label}. "
        f"This world only tells stories where the repair matches the actual wheel trouble.)"
    )


ASP_RULES = r"""
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
matches(P, F)   :- repairs(F, P).
valid(V, P, F)  :- vehicle(V), problem(P), fix(F), sensible_fix(F), matches(P, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for vehicle_id in VEHICLES:
        lines.append(asp.fact("vehicle", vehicle_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for problem_id in sorted(fix.matches):
            lines.append(asp.fact("repairs", fix_id, problem_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if "wheel" not in sample.story.lower():
            raise StoryError("smoke test story does not mention 'wheel'")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            _ = generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a bad wheel starts a quarrel, and a true repair leads to reconciliation."
    )
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        if not compatible_fix(PROBLEMS[args.problem], FIXES[args.fix]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], FIXES[args.fix]))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        problem = PROBLEMS[args.problem] if args.problem else PROBLEMS[next(iter(PROBLEMS))]
        raise StoryError(explain_rejection(problem, FIXES[args.fix]))

    combos = [
        combo for combo in valid_combos()
        if (args.vehicle is None or combo[0] == args.vehicle)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    vehicle_id, problem_id, fix_id = rng.choice(sorted(combos))
    leader_name, leader_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=leader_name)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(
        vehicle=vehicle_id,
        problem=problem_id,
        fix=fix_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not compatible_fix(problem, fix):
        raise StoryError(explain_rejection(problem, fix))

    world = tell(
        vehicle=VEHICLES[params.vehicle],
        problem=problem,
        fix=fix,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        helper_type=params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (vehicle, problem, fix) combos:\n")
        for vehicle_id, problem_id, fix_id in combos:
            print(f"  {vehicle_id:7} {problem_id:11} {fix_id}")
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
            header = f"### {p.leader_name} & {p.partner_name}: {p.vehicle}, {p.problem}, {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
