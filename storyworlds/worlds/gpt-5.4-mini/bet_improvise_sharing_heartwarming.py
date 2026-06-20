#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bet_improvise_sharing_heartwarming.py
=====================================================================

A small heartwarming storyworld about a child who makes a bet, has to
improvise, and learns that sharing can turn a problem into a warm ending.

The domain is intentionally tiny: one child, one sibling or friend, one parent,
one shared treat, one missing item, and one improvised fix. State drives the
story so the ending proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/bet_improvise_sharing_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/bet_improvise_sharing_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/bet_improvise_sharing_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/bet_improvise_sharing_heartwarming.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    missing: str
    improvise: str
    fix_action: str
    shared_help: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    bet_line: str
    bet_result: str
    bet_risk: str
    improvise_line: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_shared(world: World) -> list[str]:
    out = []
    giver = world.entities.get("share_item")
    if giver and giver.meters["shared"] >= THRESHOLD and ("shared", giver.id) not in world.fired:
        world.fired.add(("shared", giver.id))
        for eid in ("hero", "friend"):
            world.get(eid).memes["warmth"] += 1
            world.get(eid).memes["joy"] += 1
        out.append("__shared__")
    return out


def _r_better(world: World) -> list[str]:
    out = []
    if world.entities.get("problem") and world.get("problem").meters["fixed"] >= THRESHOLD and ("fixed",) not in world.fired:
        world.fired.add(("fixed",))
        world.get("hero").memes["relief"] += 1
        world.get("friend").memes["relief"] += 1
        out.append("__fixed__")
    return out


RULES = [Rule("shared", "social", _r_shared), Rule("better", "social", _r_better)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(problem: Problem, offering: Offering, plan: Plan) -> bool:
    return offering.shareable and "share" in problem.tags and plan.id in PLANS


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.id != "too_small"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_plans():
        return combos
    for pid in PROBLEMS:
        for oid in OFFERINGS:
            for pl in PLANS:
                if reasonableness_gate(PROBLEMS[pid], OFFERINGS[oid], PLANS[pl]):
                    combos.append((pid, oid, pl))
    return combos


def story_begin(world: World, hero: Entity, friend: Entity, offer: Offering, problem: Problem, plan: Plan) -> None:
    world.say(
        f"On a cozy afternoon, {hero.id} and {friend.id} were getting ready to share "
        f"{offer.phrase}. {hero.id} loved the idea of saving some for both of them."
    )
    world.say(
        f'Then {hero.id} made a playful bet: "{plan.bet_line}" '
        f'{friend.id} laughed, but the bet had a small risk if the plan went wrong.'
    )


def trouble(world: World, hero: Entity, friend: Entity, problem: Problem, offer: Offering, plan: Plan) -> None:
    hero.memes["confidence"] += 1
    world.say(
        f"Right when it was time to try, {problem.label} got in the way. "
        f"{problem.missing}"
    )
    world.say(
        f'{hero.id} blinked. "{plan.improvise_line}" '
        f"{friend.id} listened closely, because the shared treat still mattered."
    )


def improvise_fix(world: World, hero: Entity, friend: Entity, problem: Problem, plan: Plan, offer: Offering) -> None:
    world.get("problem").meters["fixed"] += 1
    world.get("share_item").meters["shared"] += 1
    world.say(
        f"So {hero.id} had to improvise. {problem.improvise} "
        f"{problem.fix_action}. {problem.shared_help}"
    )
    propagate(world, narrate=False)


def warm_ending(world: World, hero: Entity, friend: Entity, plan: Plan, offer: Offering) -> None:
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"In the end, {hero.id} kept the bet in a gentle way: {plan.bet_result}. "
        f"{friend.id} got a share too, and the last bite was enjoyed together."
    )
    world.say(
        f"The room felt softer after that. {plan.ending}"
    )


def tell(problem: Problem, offering: Offering, plan: Plan, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, parent_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    share_item = world.add(Entity(id="share_item", label=offering.label))
    problem_ent = world.add(Entity(id="problem", label=problem.label))
    world.facts.update(hero=hero, friend=friend, parent=parent, offer=offering, problem=problem, plan=plan)

    story_begin(world, hero, friend, offering, problem, plan)
    world.para()
    trouble(world, hero, friend, problem, offering, plan)
    world.para()
    improvise_fix(world, hero, friend, problem, plan, offering)
    warm_ending(world, hero, friend, plan, offering)

    world.facts.update(shared=share_item.meters["shared"] >= THRESHOLD, fixed=problem_ent.meters["fixed"] >= THRESHOLD)
    return world


PROBLEMS = {
    "broken_box": Problem(
        "broken_box", "the snack box lid broke", "the treats kept slipping out",
        "they stacked the pieces in a new way", "tape the corners together",
        "They shared the last cookie while one person held the box steady.",
        tags={"sharing", "fix"},
    ),
    "too_few_chairs": Problem(
        "too_few_chairs", "there were not enough chairs", "one guest had nowhere to sit",
        "they found a blanket and made a little picnic place on the floor",
        "spread the blanket and add a cushion",
        "That made room for everybody to sit close and share.",
        tags={"sharing", "space"},
    ),
    "rain_delay": Problem(
        "rain_delay", "rain started tapping the window", "the walk would take too long",
        "they improvised a cozy inside picnic instead",
        "move the picnic under the table",
        "Soon everyone was sharing food, stories, and a dry place to smile.",
        tags={"sharing", "weather"},
    ),
}

OFFERINGS = {
    "cookies": Offering("cookies", "cookies", "a plate of cookies", True, tags={"sharing"}),
    "berries": Offering("berries", "berries", "a bowl of berries", True, tags={"sharing"}),
    "bread": Offering("bread", "bread", "warm bread slices", True, tags={"sharing"}),
}

PLANS = {
    "promise": Plan(
        "promise",
        "I bet I can make this work for both of us if I promise to share evenly.",
        "the bet turned into a promise, and both children smiled",
        "if the plan failed, somebody might feel left out",
        "Let's improvise and make a better share of it.",
        "By the time they sat down, nobody felt left out at all.",
        tags={"bet", "improvise", "sharing"},
    ),
    "kind_swap": Plan(
        "kind_swap",
        "I bet we can swap ideas and make it fair.",
        "the bet ended with a fair swap and two happy faces",
        "if they rushed, one friend might get less",
        "We can improvise with what we have.",
        "The shared snack felt even sweeter after that.",
        tags={"bet", "improvise", "sharing"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Tara", "Nina", "Ruby", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Leo", "Owen", "Theo"]


@dataclass
class StoryParams:
    problem: str
    offering: str
    plan: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "sharing": [("What does it mean to share?",
                 "Sharing means letting other people have some too, so everyone can enjoy it.")],
    "bet": [("What is a bet?",
             "A bet is when someone says they can do something and wants to see if they can.")],
    "improvise": [("What does improvise mean?",
                  "To improvise means to make a new plan with what you have when the first idea does not work.")],
    "cookie": [("Why do cookies get shared?",
                "Cookies are often shared because they are tasty and small enough for everyone to enjoy a piece.")],
    "berries": [("Why are berries good for sharing?",
                 "Berries are easy to divide into little portions, so lots of people can have some.")],
    "bread": [("Why can bread be shared easily?",
                "Bread can be broken or sliced into pieces, so it is simple to share.")],
}
KNOWLEDGE_ORDER = ["sharing", "bet", "improvise", "cookie", "berries", "bread"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the words "{f["plan"].id}" and "improvise".',
        f"Tell a gentle story where {f['hero'].id} makes a bet, has to improvise, and ends up sharing with {f['friend'].id}.",
        f"Write a cozy story about {f['offer'].phrase} that becomes a sharing moment when something does not go as planned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, parent, offer, problem, plan = f["hero"], f["friend"], f["parent"], f["offer"], f["problem"], f["plan"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, with {parent.label_word} nearby to help keep things kind."),
        ("What did they want to share?",
         f"They wanted to share {offer.phrase}. That is what made the story feel warm from the start."),
        ("What went wrong?",
         f"{problem.label}. {problem.missing}"),
        ("What did {0} do when the first idea did not work?".format(hero.id),
         f"{hero.id} had to improvise. {problem.improvise} {problem.fix_action}."),
    ]
    if f.get("shared"):
        qa.append((
            "How did the story end?",
            f"It ended with sharing, and everyone got some. {plan.ending}"
        ))
    qa.append((
        "Why was the bet a good idea in the end?",
        f"It nudged {hero.id} to try a kind solution, and the answer was to improvise instead of giving up. That turned the moment into sharing."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["offer"].tags) | set(world.facts["plan"].tags) | set(world.facts["problem"].tags)
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, offering: Offering, plan: Plan) -> str:
    return "(No story: the choices do not form a clear sharing-and-improvising problem.)"


def sensible_plan_ids() -> set[str]:
    return set(PLANS)


def outcome_of(params: StoryParams) -> str:
    return "shared" if params.plan in PLANS else "unsure"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for oid in OFFERINGS:
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("shareable", oid))
    for pl in PLANS:
        lines.append(asp.fact("plan", pl))
        lines.append(asp.fact("sensible", pl))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, O, L) :- problem(P), offering(O), plan(L), shareable(O), sensible(L).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming sharing storyworld with bet and improvise.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    if args.problem and args.offering and args.plan:
        if (args.problem, args.offering, args.plan) not in valid_combos():
            raise StoryError(explain_rejection(PROBLEMS[args.problem], OFFERINGS[args.offering], PLANS[args.plan]))
    combos = [c for c in valid_combos()
              if (not args.problem or c[0] == args.problem)
              and (not args.offering or c[1] == args.offering)
              and (not args.plan or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    problem, offering, plan = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(problem, offering, plan, hero, hero_gender, friend, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PROBLEMS[params.problem], OFFERINGS[params.offering], PLANS[params.plan],
                 params.hero, params.hero_gender, params.friend, params.friend_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams("broken_box", "cookies", "promise", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("too_few_chairs", "berries", "kind_swap", "Leo", "boy", "Ivy", "girl", "father"),
    StoryParams("rain_delay", "bread", "promise", "Nina", "girl", "Eli", "boy", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for t in asp_valid_combos():
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            sample = generate(p)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False) if len(samples) > 1 else samples[0].to_json())
        return

    for i, s in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        header = f"### {s.params.hero} and {s.params.friend}" if args.all else (f"### variant {i+1}" if len(samples) > 1 else "")
        emit(s, trace=args.trace, qa=args.qa, header=header)


if __name__ == "__main__":
    main()
