#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/democratic_busy_street_crossing_problem_solving_heartwarming.py
================================================================================================

A standalone storyworld for a busy street crossing tale with democratic problem
solving and a heartwarming tone.

Premise:
- A small group needs to cross a busy street.
- They must agree on a safe plan together.
- The story includes a democratic choice and a kind helper.
- The ending proves the plan worked and everyone feels cared for.

This file follows the shared Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven narration
- explicit reasonableness gate
- inline ASP twin and Python parity verification
- prompts, story QA, and world-knowledge QA generated from world state
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Crossing:
    id: str
    place: str
    adjective: str
    noise: str
    feature: str
    waiting_word: str
    signal_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    risk_word: str
    dangerous: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    sense: int
    safety: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


@dataclass
class StoryParams:
    crossing: str
    hazard: str
    plan: str
    helper: str
    hero: str
    hero_gender: str
    helper_gender: str
    parent: str
    trait: str
    crowd_size: int = 4
    delay: int = 0
    seed: Optional[int] = None


CROWD_LABELS = {2: "a small crowd", 3: "a few neighbors", 4: "a little group", 5: "a busy little group", 6: "a patient crowd"}
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Finn", "Theo", "Eli", "Owen", "Max"]
TRAITS = ["careful", "kind", "thoughtful", "calm", "patient", "gentle"]


CROSSINGS = {
    "busy_street": Crossing(
        id="busy_street",
        place="a busy street crossing",
        adjective="busy",
        noise="cars hummed and buses rumbled by",
        feature="crosswalk",
        waiting_word="the curb",
        signal_word="the walk signal",
        tags={"busy", "street", "crossing"},
    ),
    "school_corner": Crossing(
        id="school_corner",
        place="the busy corner by the school",
        adjective="busy",
        noise="cars zipped past and bicycles rang their bells",
        feature="crosswalk",
        waiting_word="the curb",
        signal_word="the walk sign",
        tags={"busy", "street", "crossing"},
    ),
    "market_crossing": Crossing(
        id="market_crossing",
        place="the crossing by the market",
        adjective="crowded",
        noise="cars rolled by, and shoppers hurried with bags",
        feature="crosswalk",
        waiting_word="the curb",
        signal_word="the walk signal",
        tags={"busy", "street", "crossing"},
    ),
}

HAZARDS = {
    "ball": Hazard(id="ball", label="a rolling ball", risk_word="might bounce into the street", tags={"street", "rolling"}),
    "kite": Hazard(id="kite", label="a runaway kite", risk_word="might tug someone off balance", tags={"street", "wind"}),
    "pigeon_feeders": Hazard(id="pigeon_feeders", label="some tossed crumbs", risk_word="might draw birds into the road", tags={"street", "crowd"}),
    "spilled_books": Hazard(id="spilled_books", label="a stack of dropped library books", risk_word="might make everyone hurry and bump", tags={"street", "crowd"}),
}

PLANS = {
    "count_and_hold": Plan(
        id="count_and_hold",
        label="count together, hold hands, and cross as one line",
        sense=3,
        safety=4,
        text="counted together, held hands, and crossed as one line when the signal turned safe",
        fail="counted, but the children were too rushed to keep the line tidy",
        qa_text="counted together, held hands, and crossed as one line",
        tags={"safe", "together"},
    ),
    "stop_and_wave": Plan(
        id="stop_and_wave",
        label="stop, wave, and wait for a clear gap",
        sense=3,
        safety=3,
        text="stopped, waved to the driver, and waited for a clear gap before stepping out",
        fail="stopped and waved, but the gap was too small and the plan broke apart",
        qa_text="stopped, waved, and waited for a clear gap",
        tags={"safe", "wait"},
    ),
    "ask_guard": Plan(
        id="ask_guard",
        label="ask the crossing guard for help",
        sense=4,
        safety=5,
        text="asked the crossing guard for help, listened carefully, and crossed when it was safe",
        fail="asked for help, but still rushed before listening to the answer",
        qa_text="asked the crossing guard for help and listened carefully",
        tags={"safe", "helper"},
    ),
    "line_up": Plan(
        id="line_up",
        label="line up by the curb and take turns",
        sense=3,
        safety=4,
        text="lined up by the curb, took turns, and crossed neatly together",
        fail="lined up, but one child broke the line and stepped forward too soon",
        qa_text="lined up by the curb and took turns",
        tags={"safe", "turns"},
    ),
}

REJECTED_PLANS = {
    "dash": Plan(id="dash", label="dash straight across without waiting", sense=1, safety=1, text="", fail="", qa_text="", tags={"unsafe"}),
}

PARENT_TYPES = ["mother", "father", "grandmother", "grandfather"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CROSSINGS:
        for h in HAZARDS:
            for p in PLANS:
                if reasonableness_gate(CROSSINGS[c], HAZARDS[h], PLANS[p]):
                    combos.append((c, h, p))
    return combos


def reasonableness_gate(crossing: Crossing, hazard: Hazard, plan: Plan) -> bool:
    return crossing.adjective in {"busy", "crowded"} and hazard.dangerous and plan.sense >= 3


def best_plan() -> Plan:
    return max(PLANS.values(), key=lambda p: p.safety)


def plan_success(plan: Plan, crowd_size: int, delay: int) -> bool:
    return plan.safety + 1 >= 4 + max(0, crowd_size - 4) + delay


def story_oops(plan: Plan, crowd_size: int, delay: int) -> bool:
    return not plan_success(plan, crowd_size, delay)


def _rule_calm(world: World) -> list[str]:
    out = []
    if world.get("hero").memes["worry"] >= THRESHOLD and "calm" not in world.fired:
        world.fired.add(("calm",))
        world.get("hero").memes["calm"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", "social", _rule_calm)]


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
        for s in produced:
            world.say(s)
    return produced


def predict_plan(world: World, plan: Plan, crowd_size: int, delay: int) -> dict:
    return {"success": plan_success(plan, crowd_size, delay), "calm": True}


def introduce(world: World, hero: Entity, helper: Entity, crossing: Crossing, crowd_size: int) -> None:
    world.say(
        f"At {crossing.place}, {crossing.noise}, and {CROWD_LABELS.get(crowd_size, 'a crowd')} waited to cross."
    )
    world.say(
        f"{hero.id} stood with {helper.id}, and both of them looked at {crossing.signal_word} with careful eyes."
    )


def pose_problem(world: World, hero: Entity, hazard: Hazard, crossing: Crossing) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then {hazard.label} made the moment tricky, because it {hazard.risk_word} near the {crossing.feature}."
    )
    world.say(f"{hero.id} frowned and said, \"We need a safe plan.\"")


def democratic_talk(world: World, hero: Entity, helper: Entity, parent: Entity, plan: Plan) -> None:
    hero.memes["fairness"] += 1
    helper.memes["fairness"] += 1
    parent.memes["warmth"] += 1
    world.say(
        f'The three of them held a little democratic vote. {hero.id} shared one idea, {helper.id} shared another, '
        f'and {parent.label_word} listened to both before choosing {plan.label}.'
    )


def carry_out(world: World, hero: Entity, helper: Entity, parent: Entity, crossing: Crossing, plan: Plan) -> None:
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and helped them {plan.text}."
    )


def ending_good(world: World, hero: Entity, helper: Entity, parent: Entity, crossing: Crossing) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On the far side, everyone laughed softly, and {parent.label_word} gave both children a proud hug."
    )
    world.say(
        f"The street was still busy behind them, but the little group had crossed together, safe and calm."
    )


def ending_bad(world: World, hero: Entity, helper: Entity, parent: Entity, crossing: Crossing) -> None:
    world.say(
        f"The plan fell apart for a moment, so {parent.label_word} guided them back to {crossing.waiting_word} and tried again."
    )
    world.say(
        f"This time they crossed slowly, and the busy street did not win."
    )


def tell(crossing: Crossing, hazard: Hazard, plan: Plan, crowd_size: int, delay: int,
         hero_name: str = "Mia", hero_gender: str = "girl", helper_name: str = "Ben",
         helper_gender: str = "boy", parent_type: str = "mother", trait: str = "careful") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.facts.update(crossing=crossing, hazard=hazard, plan=plan, crowd_size=crowd_size, delay=delay,
                       hero=hero, helper=helper, parent=parent)

    introduce(world, hero, helper, crossing, crowd_size)
    world.para()
    pose_problem(world, hero, hazard, crossing)
    democratic_talk(world, hero, helper, parent, plan)
    world.para()
    if plan_success(plan, crowd_size, delay):
        carry_out(world, hero, helper, parent, crossing, plan)
        ending_good(world, hero, helper, parent, crossing)
        outcome = "safe"
    else:
        world.say(f"They tried to {plan.label}, but the crowd and timing made it hard.")
        ending_bad(world, hero, helper, parent, crossing)
        outcome = "recover"
    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about {f['crossing'].place} where children solve a crossing problem together and include the word \"democratic\".",
        f"Tell a gentle story set at {f['crossing'].place} where {f['hero'].id}, {f['helper'].id}, and a parent make a democratic choice about how to cross safely.",
        f"Write a problem-solving story for a child where a busy street crossing becomes safe because everyone listens kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    crossing, hazard, plan = f["crossing"], f["hazard"], f["plan"]
    answers = [
        QAItem(
            question="What problem did the characters need to solve?",
            answer=f"They needed to cross {crossing.place} safely while staying together. The street was busy, so they had to choose a careful plan instead of rushing."
        ),
        QAItem(
            question="How was the choice democratic?",
            answer=f"{hero.id} shared an idea, {helper.id} shared another, and {parent.label_word} listened to both before they chose {plan.label}. That made the decision fair and democratic."
        ),
        QAItem(
            question="Why was the hazard important?",
            answer=f"{hazard.label.capitalize()} made the crossing harder because it could {hazard.risk_word}. The family needed a plan that kept everyone calm and out of the road."
        ),
    ]
    if f["outcome"] == "safe":
        answers.append(QAItem(
            question="How did the story end?",
            answer=f"They crossed safely and ended up smiling on the other side. The ending is heartwarming because the group worked together and the parent gave them a proud hug."
        ))
    else:
        answers.append(QAItem(
            question="How did they recover when the first try did not work?",
            answer=f"They stepped back, listened again, and tried once more with {parent.label_word}'s help. That second try turned the worry into a safe crossing."
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does democratic mean?",
            answer="Democratic means people get a fair chance to share ideas and help make a choice together."
        ),
        QAItem(
            question="Why should children wait at a busy street crossing?",
            answer="They should wait because cars and buses move quickly, and a busy street can be dangerous if people rush."
        ),
        QAItem(
            question="What is a good thing to do when crossing a street?",
            answer="A good thing to do is stay close to a trusted grown-up, look both ways, and cross only when it is safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(crossing="busy_street", hazard="ball", plan="count_and_hold", helper="Ben", hero="Mia", hero_gender="girl", helper_gender="boy", parent="mother", trait="careful", crowd_size=4, delay=0, seed=1),
    StoryParams(crossing="school_corner", hazard="kite", plan="ask_guard", helper="Lily", hero="Owen", hero_gender="boy", helper_gender="girl", parent="father", trait="kind", crowd_size=5, delay=0, seed=2),
    StoryParams(crossing="market_crossing", hazard="pigeon_feeders", plan="line_up", helper="Ava", hero="Theo", hero_gender="boy", helper_gender="girl", parent="grandmother", trait="patient", crowd_size=6, delay=1, seed=3),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and args.plan in REJECTED_PLANS:
        raise StoryError("That plan is too unsafe for a heartwarming crossing story.")
    combos = [c for c in valid_combos()
              if (args.crossing is None or c[0] == args.crossing)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    crossing_id, hazard_id, plan_id = rng.choice(sorted(combos))
    crossing = CROSSINGS[crossing_id]
    hazard = HAZARDS[hazard_id]
    plan = PLANS[plan_id]
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != hero]
    helper = args.helper or rng.choice(helper_pool)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    crowd_size = args.crowd_size if args.crowd_size is not None else rng.randint(3, 6)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(crossing=crossing.id, hazard=hazard.id, plan=plan.id, helper=helper, hero=hero,
                       hero_gender=hero_gender, helper_gender=helper_gender, parent=parent, trait=trait,
                       crowd_size=crowd_size, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.crossing not in CROSSINGS or params.hazard not in HAZARDS or params.plan not in PLANS:
        raise StoryError("Invalid parameters.")
    world = tell(CROSSINGS[params.crossing], HAZARDS[params.hazard], PLANS[params.plan],
                 params.crowd_size, params.delay, params.hero, params.hero_gender, params.helper,
                 params.helper_gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CROSSINGS:
        lines.append(asp.fact("crossing", cid))
        lines.append(asp.fact("busy", cid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.dangerous:
            lines.append(asp.fact("dangerous", hid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, H, P) :- crossing(C), hazard(H), plan(P), busy(C), dangerous(H), sense(P, S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming democratic problem-solving storyworld at a busy street crossing.")
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--plan", choices={**PLANS, **REJECTED_PLANS})
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--crowd-size", type=int)
    ap.add_argument("--delay", type=int)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
