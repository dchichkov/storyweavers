#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hectic_square_hinder_dialogue_slice_of_life.py
==============================================================================

A small slice-of-life story world about a busy town square, a little shared task,
and a gentle obstacle that gets solved through conversation.

The seed words are built into the world itself:
- hectic: the square can get busy and noisy
- square: the setting and the central table/plaza motif
- hinder: a small obstacle can slow people down

The stories are child-facing, concrete, and state-driven. They use dialogue as a
main narrative instrument and end with a clear image proving what changed.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Place:
    id: str
    label: str
    busy: bool
    square: bool
    shelter: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    goal: str
    setup: str
    result: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hinder:
    id: str
    label: str
    problem: str
    move: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    if world.place.busy and world.place.square:
        for ent in world.entities.values():
            if ent.memes["fluster"] >= THRESHOLD:
                sig = ("settle", ent.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                ent.memes["calm"] += 1
                out.append("__quiet__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("hinder_moved"):
        for ent in world.entities.values():
            if ent.kind == "character":
                sig = ("relief", ent.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                ent.memes["relief"] += 1
                out.append("__relief__")
    return out


RULES = [Rule("settle", _r_settle), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for plan_id, plan in PLANS.items():
            for hinder_id, hinder in HINDERS.items():
                if place.square and place.busy and plan.goal in plan.tags and hinder.id in {"cart", "crate", "line"}:
                    combos.append((place_id, plan_id, hinder_id))
    return combos


@dataclass
class StoryParams:
    place: str
    plan: str
    hinder: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


PLACES = {
    "square": Place("square", "the town square", busy=True, square=True, shelter=False, tags={"square", "busy", "hectic"}),
    "cafe_square": Place("cafe_square", "the cafe square", busy=True, square=True, shelter=True, tags={"square", "hectic"}),
    "market_square": Place("market_square", "the market square", busy=True, square=True, shelter=False, tags={"square", "busy", "hectic"}),
}

PLANS = {
    "snack_stand": Plan("snack_stand", "set up a snack stand", "a tiny table with cups and napkins", "the table looked ready for visitors", "cups were out of place", tags={"snack", "table", "square"}),
    "chalk_mural": Plan("chalk_mural", "draw a chalk mural", "a box of chalk and a clean patch of pavement", "the pavement became a bright picture", "the chalk could get stepped on", tags={"chalk", "square"}),
    "flower_fix": Plan("flower_fix", "arrange flower pots", "three pots and a watering can", "the pots made the corner look cheerful", "the pots might get knocked", tags={"flowers", "square"}),
}

HINDERS = {
    "cart": Hinder("cart", "a hand cart", "it blocked the path", "roll it beside the bench", tags={"cart", "hinder"}),
    "crate": Hinder("crate", "a crate", "it sat in the middle of the square", "carry it to the wall", tags={"crate", "hinder"}),
    "line": Hinder("line", "a line of people", "it made the walkway tight", "make a little side path", tags={"line", "hinder"}),
}

RESPONSES = {
    "move_cart": Response("move_cart", 3, "pushed the hand cart aside and opened a clear space", "tried to squeeze around it, but there was still no room", "pushed the hand cart aside and opened a clear space", tags={"cart"}),
    "carry_crate": Response("carry_crate", 3, "carried the crate to the wall together", "lifted the crate, but it was too heavy to move far", "carried the crate to the wall together", tags={"crate"}),
    "side_path": Response("side_path", 2, "made a little side path and asked people to use it", "tried to wave people through, but the path stayed tight", "made a little side path and asked people to use it", tags={"line"}),
}

CHILD_NAMES = ["Mina", "Eli", "Noa", "Tara", "Owen", "Zuri"]
HELPER_NAMES = ["Ada", "Ben", "Maya", "Leo", "Iris", "Sam"]


def explain_rejection(place: Place, plan: Plan, hinder: Hinder) -> str:
    return f"(No story: {hinder.label} does not give a good slice-of-life hindrance for {plan.goal} at {place.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a busy square and a small hindrance.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hinder", choices=HINDERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.plan is None or c[1] == args.plan)
              and (args.hinder is None or c[2] == args.hinder)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, plan, hinder = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(place=place, plan=plan, hinder=hinder, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender)


def tell(place: Place, plan: Plan, hinder: Hinder, response: Response,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    obstacle = world.add(Entity(id="obstacle", kind="thing", type=hinder.id, label=hinder.label, role="hindrance"))

    child.memes["fluster"] = 1.0
    helper.memes["care"] = 1.0

    world.say(f"It was a hectic morning in {place.label}, and {child.id} wanted to {plan.goal}.")
    world.say(f'{child.id} pointed to the square patch and said, "{plan.setup} would fit right there."')
    world.say(f'{helper.id} looked at {obstacle.label} and said, "{hinder.problem.capitalize()}."')

    world.para()
    world.say(f'{child.id} frowned. "Can we still do it?"')
    world.say(f'{helper.id} nodded. "Yes, but we need a way around the {hinder.label}."')

    world.para()
    response_text = response.text.replace("{target}", hinder.label)
    if response.id == "side_path":
        world.say(f'{helper.id} smiled. "{response_text.capitalize()}."')
    else:
        world.say(f'{helper.id} said, "{response_text.capitalize()}."')
    world.say(f'{child.id} replied, "That sounds better than trying to hinder everyone with the cart."')

    world.facts["hinder_moved"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(f"Together they {hinder.move}, and soon {plan.result}.")
    world.say(f'The square felt calmer after the hectic start, and {child.id} grinned at the neat little scene.')

    world.facts.update(
        child=child, helper=helper, obstacle=obstacle, plan=plan, hinder=hinder,
        response=response, place=place, resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "hectic", "square", and "hinder".',
        f"Tell a gentle story about {f['child'].id} and {f['helper'].id} in {f['place'].label} where a small obstacle hinders their plan, and they fix it with dialogue.",
        f'Write a child-friendly story where a busy square feels hectic at first, but the characters talk kindly and make it work.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    plan = f["plan"]
    hinder = f["hinder"]
    place = f["place"]
    return [
        ("What kind of day was it?",
         f"It was a hectic day in {place.label}, so everything felt busy at first. That made the little problem stand out more, because the square was full of movement."),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted to {plan.goal}. {child.id} had a simple plan for the square, but the obstacle made it harder to begin."),
        (f"How did {helper.id} help?",
         f"{helper.id} talked it through with {child.id} and helped move {hinder.label}. That cleared the way so the two of them could keep going without fuss."),
        ("How did the story end?",
         f"It ended with the plan finished and the square looking neat and calm again. The hectic feeling faded once the hindrance was moved aside."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does hectic mean?",
         "Hectic means very busy and a little noisy, like when many things are happening at once."),
        ("What is a square?",
         "A square is an open place with four sides or a plaza in a town where people can gather."),
        ("What does hinder mean?",
         "To hinder something means to slow it down or make it harder to do."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pl, H) :- place(P), plan(Pl), hinder(H), square(P), busy(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.square:
            lines.append(asp.fact("square", pid))
        if p.busy:
            lines.append(asp.fact("busy", pid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    for hid in HINDERS:
        lines.append(asp.fact("hinder", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos().")

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_sample(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.plan not in PLANS or params.hinder not in HINDERS:
        raise StoryError("(Invalid params.)")
    response_id = "move_cart" if params.hinder == "cart" else ("carry_crate" if params.hinder == "crate" else "side_path")
    response = RESPONSES[response_id]
    world = tell(PLACES[params.place], PLANS[params.plan], HINDERS[params.hinder], response,
                 params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(place="square", plan="snack_stand", hinder="cart", child="Mina", child_gender="girl", helper="Ada", helper_gender="girl"),
    StoryParams(place="market_square", plan="chalk_mural", hinder="line", child="Eli", child_gender="boy", helper="Sam", helper_gender="boy"),
    StoryParams(place="cafe_square", plan="flower_fix", hinder="crate", child="Tara", child_gender="girl", helper="Leo", helper_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, plan, hinder) combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        if len(samples) > 1 and not args.all:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
