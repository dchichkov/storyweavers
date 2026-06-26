#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/laundry_barrier_snuff_forest_trail_magic_twist.py
================================================================================================

A small adventure storyworld about a forest trail, a laundry barrier, and a snuff-
smoke twist resolved by magic and problem solving.

Seed premise:
A child hikes a forest trail carrying clean laundry to a cabin. A fallen log and
thick snuff from a tiny woodland lantern make the trail risky. The child and a
helper use a little magic to raise a barrier, protect the laundry, and solve the
problem before the trip can continue.

The story engine models:
- physical meters: wet, sooty, blocked, magic, carried, barrier, safe
- emotional memes: worry, courage, wonder, relief, pride

The narrative shape is classical:
setup -> problem -> twist -> problem solving -> resolution.
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SETTING_NAME = "forest trail"
STYLE = "Adventure"

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "sooty", "blocked", "magic", "carried", "barrier", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "courage", "wonder", "relief", "pride", "curiosity"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    noun: str
    smoke: str
    twist: str
    blocked_by: str
    risky_area: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class MagicTool:
    id: str
    label: str
    spell: str
    fix: str
    barrier: str
    shield: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


PLACES = {
    "forest_trail": Place(id="forest_trail", name=SETTING_NAME, affords={"snuff"}),
}

PROBLEMS = {
    "snuff": Problem(
        id="snuff",
        verb="follow the trail",
        noun="snuff",
        smoke="smoky",
        twist="the little lantern had snuffed itself out, sending a puff of dark smoke over the path",
        blocked_by="fallen branches",
        risky_area="trail",
        tags={"snuff", "smoke"},
    ),
}

PRIZES = {
    "laundry": Prize(
        id="laundry",
        label="laundry",
        phrase="a basket of clean laundry",
        region="carried",
        plural=True,
    ),
}

MAGIC = {
    "glimmer_cloak": MagicTool(
        id="glimmer_cloak",
        label="glimmer cloak",
        spell="spread a shining glimmer-cloak across the laundry",
        fix="wove a bright, shimmering cover around the basket",
        barrier="a sparkling barrier",
        shield={"sooty", "wet"},
        guards={"snuff"},
        plural=False,
    ),
    "leaf_screen": MagicTool(
        id="leaf_screen",
        label="leaf screen",
        spell="grow a leaf-screen beside the trail",
        fix="raised a leafy screen to steer the smoke away",
        barrier="a green barrier",
        shield={"sooty"},
        guards={"snuff"},
        plural=False,
    ),
}

NAMES = ["Mila", "Nico", "Tara", "Finn", "Ruby", "Eli", "Ivy", "Owen"]
HELPER_NAMES = ["Pip", "Sage", "Luna", "Bo", "Moss", "Wren"]
TRAITS = ["brave", "curious", "careful", "spirited", "gentle"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
    hero: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

def _r_smoke_soot(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "thing":
            continue
        if e.meters["sooty"] >= THRESHOLD:
            continue
        if e.carried_by and world.get(e.carried_by).meters["smoke"] >= THRESHOLD:
            sig = ("soot", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["sooty"] += 1
            if e.id == "laundry":
                e.meters["safe"] = 0
            out.append(f"The smoke left {e.label} a little sooty.")
    return out


def _r_barrier_protects(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["barrier"] < THRESHOLD:
        return out
    for e in world.entities.values():
        if e.id == "laundry" and e.meters["sooty"] >= THRESHOLD:
            sig = ("shield", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["safe"] += 1
            out.append("The magic barrier kept the laundry safe.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["safe"] >= THRESHOLD and hero.memes["worry"] >= THRESHOLD:
        sig = ("calm",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["worry"] = 0
        hero.memes["relief"] += 1
        out.append("The worry faded once the plan worked.")
    return out


RULES = [_r_smoke_soot, _r_barrier_protects, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            res = rule(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def select_magic(problem: Problem, prize: Prize) -> Optional[MagicTool]:
    for m in MAGIC.values():
        if problem.id in m.guards and prize.region == "carried":
            return m
    return None


def reasonableness_gate(problem: Problem, prize: Prize) -> bool:
    return prize.region == "carried" and bool(select_magic(problem, prize))


def explain_rejection(problem: Problem, prize: Prize) -> str:
    return (
        f"(No story: this problem does not reasonably threaten {prize.label}, "
        f"or no magic barrier in the registry can protect it.)"
    )


def _hero_intro(world: World, hero: Entity, trait: str) -> None:
    world.say(f"{hero.id} was a {trait} {hero.type} who loved adventure on the forest trail.")


def _setup(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"One morning, {hero.id} packed {hero.pronoun('possessive')} {prize.label} "
        f"and set out with {helper.id} to cross the {SETTING_NAME}."
    )


def _twist(world: World, problem: Problem, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["worry"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"Halfway down the trail, {problem.twist}. "
        f"{hero.id} clutched {hero.pronoun('possessive')} {prize.label} tighter."
    )
    world.say(
        f"Now the path smelled smoky, and {hero.id} worried the laundry would be ruined."
    )


def _problem_solving(world: World, problem: Problem, hero: Entity, helper: Entity, prize: Entity, magic: MagicTool) -> None:
    hero.memes["courage"] += 1
    hero.memes["wonder"] += 1
    helper.memes["pride"] += 1
    hero.meters["barrier"] += 1
    world.say(
        f"Then {helper.id} whispered a magic word, and {hero.id} used it to {magic.spell}."
    )
    world.say(
        f"Together they {magic.fix}, building {magic.barrier} between the smoke and the basket."
    )
    propagate(world, narrate=True)
    if prize.meters["safe"] >= THRESHOLD:
        world.say(
            f"The snuff drifted past, but the laundry stayed fresh and clean."
        )


def _resolution(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"At the end, {hero.id} kept walking with {helper.id}, carrying the laundry safely down the trail."
    )
    world.say(
        f"The forest looked bright again, and the clean basket bounced along like a little treasure."
    )


def tell(place: Place, problem: Problem, prize_cfg: Prize, hero_name: str, hero_type: str, helper_name: str, trait: str) -> World:
    world = World(place.name)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="character", label=helper_name))
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        type="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
        carried_by=hero.id,
    ))

    _hero_intro(world, hero, trait)
    _setup(world, hero, helper, prize)
    world.para()
    _twist(world, problem, hero, helper, prize)
    magic = select_magic(problem, prize)
    if magic is None:
        raise StoryError(explain_rejection(problem, prize))
    world.para()
    _problem_solving(world, problem, hero, helper, prize, magic)
    world.para()
    _resolution(world, hero, helper, prize)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "prize": prize,
        "problem": problem,
        "magic": magic,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    problem = f["problem"]
    return [
        f'Write a short Adventure story set on a {SETTING_NAME} about {hero.label} protecting {prize.label} from {problem.id}.',
        f"Tell a child-friendly story where a forest trail twist creates trouble, and magic helps solve the laundry problem.",
        f'Write a simple story including the words "laundry", "barrier", and "snuff" with a magical problem-solving ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    problem: Problem = f["problem"]
    magic: MagicTool = f["magic"]
    return [
        QAItem(
            question=f"What was {hero.label} carrying on the forest trail?",
            answer=f"{hero.label} was carrying {prize.phrase} on the forest trail.",
        ),
        QAItem(
            question=f"What was the problem that turned the walk into a twist?",
            answer=f"The twist came when {problem.twist}. That made the trail smoky and risky for the laundry.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the problem?",
            answer=f"They used magic to {magic.spell} and made {magic.barrier} between the smoke and the laundry.",
        ),
        QAItem(
            question=f"How did the story end for the laundry?",
            answer="The laundry stayed clean and safe, and the children finished the trail with relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barrier?",
            answer="A barrier is something that blocks or protects, like a fence, wall, or shield.",
        ),
        QAItem(
            question="What is snuff in a story like this?",
            answer="Snuff can mean something going out, or the smoky puff left after a small flame stops burning.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means finding a smart way to fix trouble instead of giving up.",
        ),
        QAItem(
            question="What is magic in an adventure story?",
            answer="Magic is a special kind of impossible-seeming power that can help characters do amazing things.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: laundry, barrier, and snuff on a forest trail.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.problem and args.prize:
        pr = PRIZES[args.prize]
        prob = PROBLEMS[args.problem]
        if not reasonableness_gate(prob, pr):
            raise StoryError(explain_rejection(prob, pr))

    place = args.place or "forest_trail"
    problem = args.problem or "snuff"
    prize = args.prize or "laundry"
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, prize=prize, hero=hero, hero_type=hero_type, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        PROBLEMS[params.problem],
        PRIZES[params.prize],
        params.hero,
        params.hero_type,
        params.helper,
        params.trait,
    )
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


# ---------------------------------------------------------------------------
# Trace / verification
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({sig[0] for sig in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", oid))
        lines.append(asp.fact("smoke_of", oid, "snuff"))
        lines.append(asp.fact("blocks", oid, prob.blocked_by))
    for lid, prize in PRIZES.items():
        lines.append(asp.fact("prize", lid))
        lines.append(asp.fact("worn_on", lid, prize.region))
        if prize.plural:
            lines.append(asp.fact("plural", lid))
    for mid, mag in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        for g in sorted(mag.guards):
            lines.append(asp.fact("guards", mid, g))
        for s in sorted(mag.shield):
            lines.append(asp.fact("shields", mid, s))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- prize(P), worn_on(P, carried).
has_fix(P) :- prize_at_risk(P), magic(M), guards(M, snuff), shields(M, sooty).
valid_story(forest_trail, snuff, P) :- place(forest_trail), problem(snuff), prize(P), has_fix(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(prob, prize) and pid == "forest_trail":
                    combos.append((pid, prob_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="forest_trail", problem="snuff", prize="laundry", hero="Mila", hero_type="girl", helper="Pip", trait="curious"),
    StoryParams(place="forest_trail", problem="snuff", prize="laundry", hero="Finn", hero_type="boy", helper="Sage", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero}: {p.problem} on {p.place} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
