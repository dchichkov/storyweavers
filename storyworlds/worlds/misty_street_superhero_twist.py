#!/usr/bin/env python3
"""
storyworlds/worlds/misty_street_superhero_twist.py
==================================================

Seed prompt used:
    Words: misty street
    Features: Twist
    Style: Superhero Story

Source tale written from the seed
----------------------------------
Mina tied a towel around her shoulders and called herself Captain Kind. On a
misty street after breakfast, she saw two green eyes blinking near the opposite
curb and heard a tiny squeak. "A trapped moon monster!" she whispered. She
wanted to race across and save it before it vanished.

Dad stopped her at the curb. "The street is too misty. Drivers and scooters
cannot see a small superhero in a towel cape." Mina frowned, because heroes did
not like waiting. Dad gave her a bright sash, pressed the crossing button, and
walked with her when the cars stopped.

The twist was waiting under a newspaper box: not a monster, but a kitten wearing
a green reflective collar. Mina carried it home in both hands. Captain Kind had
saved the day by being seen first.

This world models that story as a small simulation: a child sees a suspicious
clue across a low-visibility street, a grown-up predicts the traffic risk on a
copy of the world, conflict rises when the child tries to rush, and a safety
plan is accepted only if it actually addresses visibility and crossing control.
The "monster" reveal is rendered only after the child reaches the physical clue.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def name(self) -> str:
        return self.label or self.id

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Street:
    id: str
    phrase: str
    detail: str
    visibility: int
    traffic: int
    crossing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    clue: str
    mistaken_for: str
    reveal: str
    need: str
    carry_line: str
    across: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    visible: bool
    controlled: bool
    sense: int
    offer: str
    arrival: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, street: Street) -> None:
        self.street = street
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.active_plan: Optional[Plan] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.street)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.active_plan = copy.deepcopy(self.active_plan)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _plan_protects(plan: Optional[Plan]) -> bool:
    return bool(plan and plan.visible and plan.controlled and plan.sense >= SENSE_MIN)


def _r_traffic_risk(world: World) -> list[str]:
    hero = world.entities.get("hero")
    adult = world.entities.get("adult")
    if not hero or not adult:
        return []
    if hero.meters["curb_dash"] < THRESHOLD:
        return []
    if world.street.visibility > 2 or world.street.traffic <= 0:
        return []
    if _plan_protects(world.active_plan):
        return []
    sig = ("traffic_risk", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["traffic_risk"] += 1
    adult.memes["worry"] += 1
    return []


def _r_blocked_conflict(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if not hero:
        return []
    if hero.memes["haste"] < THRESHOLD or hero.memes["blocked"] < THRESHOLD:
        return []
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    return []


def _r_reveal_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    clue = world.entities.get("clue")
    if not hero or not clue or clue.meters["reached"] < THRESHOLD:
        return []
    sig = ("reveal", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["understood"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule("traffic_risk", "physical", _r_traffic_risk),
    Rule("blocked_conflict", "social", _r_blocked_conflict),
    Rule("reveal_relief", "memeplex", _r_reveal_relief),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def clue_at_risk(street: Street, signal: Signal) -> bool:
    return signal.across and street.visibility <= 2 and street.traffic > 0


def plan_addresses(street: Street, signal: Signal, plan: Plan) -> bool:
    if not clue_at_risk(street, signal):
        return False
    return plan.sense >= SENSE_MIN and plan.visible and plan.controlled


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, street in STREETS.items():
        for cid, clue in SIGNALS.items():
            for pid, plan in PLANS.items():
                if plan_addresses(street, clue, plan):
                    out.append((sid, cid, pid))
    return out


def _dash(world: World, hero: Entity) -> None:
    hero.meters["curb_dash"] += 1
    propagate(world)


def predict_dash(world: World, hero: Entity) -> dict:
    sim = world.copy()
    _dash(sim, sim.get(hero.id))
    return {
        "risk": sim.get(hero.id).meters["traffic_risk"],
        "adult_worry": sim.get("adult").memes["worry"],
    }


def introduce(world: World, hero: Entity) -> None:
    trait = hero.traits[0] if hero.traits else "kind"
    world.say(
        f"{hero.name} was a little {trait} {hero.type} who turned every towel into "
        f"a superhero cape."
    )
    hero.memes["hero_play"] += 1


def notice_clue(world: World, hero: Entity, signal: Signal) -> None:
    world.say(
        f"One morning, {world.street.phrase} curled along the curb. "
        f"{world.street.detail}"
    )
    world.say(
        f"Across the road, {hero.name} saw {signal.clue}. "
        f'"Something like a {signal.mistaken_for} needs help!" {hero.pronoun()} whispered.'
    )
    hero.memes["desire"] += 1


def warn(world: World, adult: Entity, hero: Entity, signal: Signal) -> None:
    pred = predict_dash(world, hero)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_worry"] = pred["adult_worry"]
    if pred["risk"] >= THRESHOLD:
        world.say(
            f'{adult.label_word.capitalize()} stopped at the curb. "This street has '
            f"too much mist and motion. Drivers and scooters may not see a small "
            f'superhero rushing toward the {signal.mistaken_for}."'
        )


def rush_and_block(world: World, adult: Entity, hero: Entity) -> None:
    hero.memes["haste"] += 1
    hero.memes["blocked"] += 1
    propagate(world)
    world.say(
        f"{hero.name} bounced on {hero.pronoun('possessive')} toes, because heroes "
        f"liked being quick. {adult.label_word.capitalize()} held "
        f"{hero.pronoun('possessive')} hand before one foot left the curb."
    )
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f'{hero.name} frowned. "But heroes do not wait!"')


def choose_plan(world: World, adult: Entity, hero: Entity, plan: Plan) -> None:
    world.active_plan = plan
    hero.memes["seen"] += 1
    hero.memes["conflict"] = 0
    world.say(
        f'{adult.label_word.capitalize()} nodded toward the crossing. "{plan.offer}"'
    )
    world.say(
        f"The plan made {hero.name} bright and the path clear, so the grown-up and "
        f"the superhero crossed only when {world.street.crossing}."
    )


def reveal(world: World, hero: Entity, signal: Signal, plan: Plan) -> None:
    clue = world.get("clue")
    clue.meters["reached"] += 1
    propagate(world)
    world.say(
        f"The twist was waiting by the opposite curb: not a "
        f"{signal.mistaken_for}, but {signal.reveal}."
    )
    world.say(
        f"{hero.name} {signal.carry_line}. {plan.arrival} "
        f"The street stayed behind them, and Captain Kind had saved the day "
        f"by being seen first."
    )


def tell(street: Street, signal: Signal, plan: Plan, name: str, gender: str,
         parent_type: str, trait: str) -> World:
    world = World(street)
    hero = world.add(Entity("hero", "character", gender, name, "hero", [trait]))
    adult = world.add(Entity("adult", "character", parent_type, "the parent", "adult"))
    world.add(Entity("clue", "thing", "clue", signal.mistaken_for, attrs={"signal": signal.id}))

    introduce(world, hero)
    notice_clue(world, hero, signal)
    world.para()
    warn(world, adult, hero, signal)
    rush_and_block(world, adult, hero)
    world.para()
    choose_plan(world, adult, hero, plan)
    reveal(world, hero, signal, plan)

    world.facts.update(
        hero=hero, adult=adult, street=street, signal=signal, plan=plan,
        reached=world.get("clue").meters["understood"] >= THRESHOLD,
        conflict=hero.memes["blocked"] >= THRESHOLD,
    )
    return world


STREETS = {
    "misty": Street(
        "misty", "a misty street", "Parked cars looked soft around the edges.",
        visibility=1, traffic=2, crossing="the crossing light showed WALK",
        tags={"mist", "street", "traffic"}),
    "foggy": Street(
        "foggy", "a foggy street", "The far sidewalk looked as if someone had rubbed it with an eraser.",
        visibility=1, traffic=1, crossing="the crossing guard lifted a stop sign",
        tags={"mist", "street", "traffic"}),
    "drizzly": Street(
        "drizzly", "a drizzly street", "Umbrellas bobbed past and bicycle bells sounded close before they appeared.",
        visibility=2, traffic=2, crossing="the cars stopped at the zebra crossing",
        tags={"rain", "street", "traffic"}),
    "clear": Street(
        "clear", "a clear street", "The far curb was easy to see.",
        visibility=5, traffic=1, crossing="the crossing light showed WALK",
        tags={"street"}),
}

SIGNALS = {
    "green_eyes": Signal(
        "green_eyes", "two green eyes blinking under a newspaper box",
        "trapped moon monster", "a kitten with a green reflective collar",
        "gentle hands and a warm place", "carried the kitten home in both hands",
        tags={"cat", "reflective"}),
    "red_flash": Signal(
        "red_flash", "a red flash winking beside the storm drain",
        "tiny robot alarm", "a bicycle reflector fallen from a wheel",
        "someone to place it where riders could find it",
        "set the reflector on the dry steps of the bike shop",
        tags={"reflective", "bike"}),
    "silver_whimper": Signal(
        "silver_whimper", "a silver shape shivering beside the crossing sign",
        "lost space puppy", "a wet toy dog with a squeaker inside",
        "a washcloth and a safe return to its owner",
        "tucked the toy into the basket by the lost-and-found sign",
        tags={"toy", "rain"}),
}

PLANS = {
    "bright_sash": Plan(
        "bright_sash", "bright sash", True, True, 3,
        "Put on this bright sash, press the button, and cross with me when the cars stop.",
        "The bright sash glowed against the gray morning.",
        tags={"visibility", "crosswalk"}),
    "crossing_guard": Plan(
        "crossing_guard", "crossing guard", True, True, 3,
        "Wave to the crossing guard and keep your yellow cape where everyone can see it.",
        "The crossing guard smiled at the careful rescue team.",
        tags={"visibility", "crosswalk"}),
    "hold_hands": Plan(
        "hold_hands", "hand-holding plan", False, True, 2,
        "Hold my hand and we will hurry together.",
        "They hurried back together.",
        tags={"crosswalk"}),
    "faster_cape": Plan(
        "faster_cape", "faster cape", True, False, 1,
        "Tie the towel tighter so you can run faster.",
        "The cape streamed behind the rescue.",
        tags={"visibility"}),
}

GIRL_NAMES = ["Mina", "Ava", "Nora", "Zoe", "Lucy"]
BOY_NAMES = ["Leo", "Sam", "Max", "Theo", "Ben"]
TRAITS = ["kind", "brave", "careful", "curious", "quick"]


@dataclass
class StoryParams:
    street: str
    signal: str
    plan: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mist": [("What is mist?",
              "Mist is a cloud of tiny water drops near the ground. It can make faraway things hard to see.")],
    "traffic": [("Why should you be extra careful near traffic in mist?",
                 "Mist can hide people and cars from each other. Crossing slowly with a grown-up helps drivers see you.")],
    "reflective": [("What does reflective mean?",
                    "Something reflective bounces light back. Reflective collars, patches, and sashes help people notice you.")],
    "crosswalk": [("What is a crosswalk for?",
                   "A crosswalk is a marked place to cross the street. It tells drivers to expect people walking there.")],
    "cat": [("Why might a kitten hide near a curb?",
             "A kitten may hide when it feels cold, scared, or lost. A grown-up can help move it safely.")],
    "bike": [("Why do bicycles have reflectors?",
              "Reflectors help other people see a bicycle in dim light, which makes riding safer.")],
    "rain": [("Why do toys squeak when they get wet?",
              "Some toys have little squeakers inside. Water can press or shake them so they make funny sounds.")],
}
KNOWLEDGE_ORDER = ["mist", "traffic", "crosswalk", "reflective", "cat", "bike", "rain"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, street, signal = f["hero"], f["street"], f["signal"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes "{street.phrase}" and has a twist.',
        f"Tell a story where {hero.name}, a little {hero.type}, wants to rescue what looks like a {signal.mistaken_for}, but must cross safely first.",
        "Write a gentle superhero tale where the real heroic choice is being visible and careful before helping.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, adult, street, signal, plan = f["hero"], f["adult"], f["street"], f["signal"], f["plan"]
    pw = adult.label_word
    return [
        ("Who is the story about?",
         f"It is about {hero.name}, a little {hero.type} who pretends to be a superhero, and {hero.pronoun('possessive')} {pw}."),
        (f"What did {hero.name} think {hero.pronoun()} saw across the street?",
         f"{hero.name} thought {hero.pronoun()} saw a {signal.mistaken_for}. The mist and the small clue made it look mysterious at first."),
        (f"Why did {hero.name}'s {pw} stop {hero.pronoun('object')}?",
         f"{pw.capitalize()} stopped {hero.pronoun('object')} because {street.phrase} had low visibility and traffic. The world model predicted that rushing across could make {hero.name} hard for drivers or scooters to see."),
        ("What safety plan did they use?",
         f"They used the {plan.label}: {plan.offer} That plan addressed the danger because it made {hero.name} visible and controlled the crossing."),
        ("What was the twist?",
         f"The clue was not a {signal.mistaken_for}; it was {signal.reveal}. The rescue still mattered, but the story shows that heroes check carefully before rushing."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["street"].tags) | set(f["signal"].tags) | set(f["plan"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:7} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  active plan: {world.active_plan.id if world.active_plan else 'none'}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("misty", "green_eyes", "bright_sash", "Mina", "girl", "father", "kind"),
    StoryParams("foggy", "red_flash", "crossing_guard", "Theo", "boy", "mother", "careful"),
    StoryParams("drizzly", "silver_whimper", "bright_sash", "Nora", "girl", "mother", "brave"),
]


def explain_rejection(street: Street, signal: Signal, plan: Plan) -> str:
    if not clue_at_risk(street, signal):
        return (f"(No story: {street.phrase} does not create a hidden-traffic rescue risk for "
                f"{signal.mistaken_for}, so the warning has no honest force.)")
    if plan.sense < SENSE_MIN:
        return (f"(No story: '{plan.id}' is too weak as a safety plan. The fix must be sensible, "
                f"not just dramatic.)")
    return (f"(No story: '{plan.id}' does not solve the misty-street problem. A valid plan must "
            f"make the child visible and use a controlled crossing.)")


ASP_RULES = r"""
risk(S,C) :- signal(C), across(C), street(S), visibility(S,V), V <= 2, traffic(S,T), T > 0.
sensible(P) :- plan(P), sense(P,N), sense_min(M), N >= M.
addresses(P) :- plan(P), visible(P), controlled(P), sensible(P).
valid(S,C,P) :- risk(S,C), addresses(P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for sid, street in STREETS.items():
        lines.append(asp.fact("street", sid))
        lines.append(asp.fact("visibility", sid, street.visibility))
        lines.append(asp.fact("traffic", sid, street.traffic))
    for cid, signal in SIGNALS.items():
        lines.append(asp.fact("signal", cid))
        if signal.across:
            lines.append(asp.fact("across", cid))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, plan.sense))
        if plan.visible:
            lines.append(asp.fact("visible", pid))
        if plan.controlled:
            lines.append(asp.fact("controlled", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a misty-street superhero rescue with a twist.")
    ap.add_argument("--street", choices=STREETS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--plan", choices=PLANS)
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
    if args.street and args.signal and args.plan:
        st, sg, pl = STREETS[args.street], SIGNALS[args.signal], PLANS[args.plan]
        if not plan_addresses(st, sg, pl):
            raise StoryError(explain_rejection(st, sg, pl))
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        st = STREETS[args.street] if args.street else STREETS["misty"]
        sg = SIGNALS[args.signal] if args.signal else SIGNALS["green_eyes"]
        raise StoryError(explain_rejection(st, sg, PLANS[args.plan]))
    combos = [c for c in valid_combos()
              if (args.street is None or c[0] == args.street)
              and (args.signal is None or c[1] == args.signal)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    street, signal, plan = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(street, signal, plan, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(STREETS[params.street], SIGNALS[params.signal], PLANS[params.plan],
                 params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (street, signal, plan) combos:\n")
        for street, signal, plan in combos:
            print(f"  {street:8} {signal:14} {plan}")
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
            header = f"### {p.name}: {p.signal} on the {p.street} street ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
