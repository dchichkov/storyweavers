#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bear_alpha_lawyer_transformation_tall_tale.py
===============================================================================

A standalone story world for a tall-tale domain where a bear, an alpha, and a
lawyer cross a windy frontier, and a transformation changes what the bear can do.

Premise
-------
A small bear wants to be brave enough to help a town that is arguing with its
alpha leader. A lawyer arrives with a sensible plan, but the tall tale turns on a
big transformation: the bear changes from timid to towering, the trouble changes
into a bridgeable problem, and the ending proves the change in both body and mood.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- uses typed entities with physical meters and emotional memes
- generates story-grounded QA from simulated world state
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
TALL_TALE_SIZE = 3.0
BRAVERY_START = 2.0


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
        female = {"girl", "woman", "mother", "mom", "lawyer"}
        male = {"boy", "man", "father", "dad", "bear", "alpha", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    tall: str
    echo: str
    triggers: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    source: str
    form: str
    size_gain: float
    mood_gain: float
    effect: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    pressure: float
    risk: str
    question: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    label: str
    sense: int
    power: float
    verb: str
    result: str
    qa_text: str
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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_grow(world: World) -> list[str]:
    out = []
    b = world.get("bear")
    if b.memes["wonder"] >= THRESHOLD and b.meters["size"] < TALL_TALE_SIZE:
        sig = ("grow",)
        if sig not in world.fired:
            world.fired.add(sig)
            b.meters["size"] = TALL_TALE_SIZE
            b.memes["courage"] += 2
            out.append("__grow__")
    return out


def _r_settle(world: World) -> list[str]:
    out = []
    if world.get("town").meters["peace"] >= THRESHOLD and "settle" not in world.fired:
        world.fired.add(("settle",))
        for eid in ("alpha", "lawyer"):
            world.get(eid).memes["relief"] += 1
        out.append("__settle__")
    return out


CAUSAL_RULES = [Rule("grow", "transformation", _r_grow), Rule("settle", "social", _r_settle)]


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


def reasonableness_gate(problem: Problem, trans: Transformation, response: Resolution) -> bool:
    return response.sense >= 2 and problem.pressure >= 1.0 and trans.size_gain >= 1.0


def sensible_responses() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= 2]


def choose_problem() -> Problem:
    return next(iter(PROBLEMS.values()))


def predict_outcome(world: World, trans: Transformation, response: Resolution) -> dict:
    sim = world.copy()
    do_transformation(sim, trans, narrate=False)
    do_resolution(sim, response, narrate=False)
    return {"peace": sim.get("town").meters["peace"], "bigness": sim.get("bear").meters["size"]}


def do_opening(world: World, bear: Entity, alpha: Entity, lawyer: Entity, place: Place) -> None:
    bear.memes["hope"] += 1
    world.say(
        f"On a long-vanished afternoon, a small bear, an alpha, and a lawyer met "
        f"at {place.name}. {place.tall}."
    )
    world.say(
        f"{bear.id} was little enough to fit under a wagon wheel, but {bear.id} "
        f"kept looking at the sky as if it had a ladder hidden in it."
    )
    world.say(
        f"The {alpha.type} stood like a flagpole in a gale, and the lawyer held "
        f"a paper stack that fluttered like a flock of white birds."
    )


def do_problem(world: World, bear: Entity, alpha: Entity, lawyer: Entity, problem: Problem) -> None:
    world.say(
        f"The trouble was simple and mighty: {alpha.id} and the townsfolk were "
        f"stuck in a quarrel over {problem.label}. {problem.risk}"
    )
    world.say(
        f"The lawyer read the rules twice, then said, \"We need a fair answer, "
        f"and we need it before the sun goes down.\""
    )
    bear.memes["worry"] += 1
    lawyer.memes["logic"] += 1


def do_transformation(world: World, trans: Transformation, narrate: bool = True) -> None:
    bear = world.get("bear")
    bear.memes["wonder"] += 1
    bear.meters["size"] += trans.size_gain
    bear.memes["courage"] += trans.mood_gain
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"Then the tall tale turned its wheel. {bear.id} felt the change and "
            f"{trans.effect}."
        )


def do_warning(world: World, lawyer: Entity, problem: Problem) -> None:
    lawyer.memes["care"] += 1
    world.say(
        f"The lawyer pointed at the trouble and warned that if nobody listened, "
        f"{problem.question}"
    )


def do_resolution(world: World, response: Resolution, narrate: bool = True) -> None:
    bear = world.get("bear")
    alpha = world.get("alpha")
    lawyer = world.get("lawyer")
    town = world.get("town")
    if response.id == "bridge":
        town.meters["peace"] += response.power
        bear.memes["pride"] += 1
    elif response.id == "outtalk":
        town.meters["peace"] += response.power
        alpha.memes["respect"] += 1
    else:
        town.meters["peace"] += response.power / 2
    if narrate:
        world.say(
            f"{lawyer.id} {response.verb} the matter, and {response.result}."
        )
    propagate(world, narrate=narrate)


def do_ending(world: World, trans: Transformation) -> None:
    bear = world.get("bear")
    alpha = world.get("alpha")
    town = world.get("town")
    world.say(
        f"In the end, {bear.id} stood as {bear.meters['size']:.0f} times its old "
        f"size, and nobody called it little anymore."
    )
    world.say(
        f"{alpha.id} tipped {alpha.id}'s great head once, the lawyer folded the "
        f"papers, and the town shone peaceful under the long evening."
    )
    world.say(trans.ending_image)


def tell(place: Place, problem: Problem, trans: Transformation, response: Resolution,
         bear_name: str = "bear", alpha_name: str = "alpha", lawyer_name: str = "lawyer") -> World:
    world = World()
    bear = world.add(Entity("bear", kind="character", type="bear", label=bear_name, role="hero"))
    alpha = world.add(Entity("alpha", kind="character", type="wolf", label=alpha_name, role="leader"))
    lawyer = world.add(Entity("lawyer", kind="character", type="lawyer", label=lawyer_name, role="helper"))
    town = world.add(Entity("town", type="town", label="the town"))

    bear.meters["size"] = 1.0
    bear.memes["bravery"] = BRAVERY_START
    alpha.meters["authority"] = 2.0
    lawyer.memes["logic"] = 1.0
    town.meters["peace"] = 0.0

    do_opening(world, bear, alpha, lawyer, place)
    world.para()
    do_problem(world, bear, alpha, lawyer, problem)
    do_warning(world, lawyer, problem)
    world.para()
    do_transformation(world, trans)
    world.para()
    do_resolution(world, response)
    world.para()
    do_ending(world, trans)

    world.facts.update(place=place, problem=problem, trans=trans, response=response,
                       bear=bear, alpha=alpha, lawyer=lawyer, town=town)
    return world


PLACES = {
    "ridge": Place("ridge", "the windy ridge", "The ridge was so tall the clouds wore hats.", {"wind"}),
    "court": Place("court", "the prairie court", "The court stood high as a barn on stilts.", {"law"}),
    "harbor": Place("harbor", "the salt harbor", "The harbor masts leaned like old giants.", {"sea"}),
}

PROBLEMS = {
    "dispute": Problem("dispute", "a land line", 1.0, "A fence could split a pasture and a friendship alike.", "what would happen if the line stayed unfair?", {"law"}),
    "storm": Problem("storm", "a storm warning", 1.0, "The wind could bully the papers right out of town.", "who would keep the town calm?", {"wind"}),
}

TRANSFORMATIONS = {
    "grow": Transformation("grow", "bear", "giant bear", 3.0, 2.0, "grew taller than the fence and broader than the barn",
                           "The bear's shadow covered the road like a quilt.", {"transformation"}),
    "crown": Transformation("crown", "bear", "judge-bear", 2.0, 1.0, "found a hat big enough to hold the whole argument",
                            "The bear wore the hat and the brim cast a brave circle on the dirt.", {"transformation"}),
}

RESOLUTIONS = {
    "bridge": Resolution("bridge", "build a bridge of kind words", 3, 2.0, "built", "the sides met in the middle",
                         "built a bridge of kind words over the argument", {"law"}),
    "outtalk": Resolution("outtalk", "speak the truth plain", 3, 2.0, "spoke", "the alpha nodded and the quarrel softened",
                          "spoke the truth plain and the alpha listened", {"law"}),
    "shine": Resolution("shine", "let the bear's size calm the crowd", 2, 1.0, "shone", "the crowd fell quiet",
                        "let the bear's new size calm the crowd", {"transformation"}),
}

GIRL_NAMES = ["Mabel", "June", "Ivy", "Nora"]
BOY_NAMES = ["Otis", "Cliff", "Beau", "Silas"]


@dataclass
class StoryParams:
    place: str
    problem: str
    transformation: str
    response: str
    bear_name: str
    alpha_name: str
    lawyer_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for pr in PROBLEMS:
            for t in TRANSFORMATIONS:
                if reasonableness_gate(PROBLEMS[pr], TRANSFORMATIONS[t], RESOLUTIONS["bridge"]):
                    combos.append((p, pr, t))
    return combos


KNOWLEDGE = {
    "bear": [("What is a bear?", "A bear is a big animal with fur, strong paws, and a nose that likes to sniff the world.")],
    "alpha": [("What does alpha mean in a story about wolves?", "Alpha means the leader of the group, the one the others look to when deciding what to do.")],
    "lawyer": [("What does a lawyer do?", "A lawyer helps people with rules, fair answers, and arguments.")],
    "transformation": [("What is a transformation?", "A transformation is a big change from one form or state into another.")],
    "law": [("Why do people use rules?", "Rules help people share, decide fairly, and keep trouble from growing.")],
    "wind": [("What can strong wind do?", "Strong wind can push hats, shake doors, and make papers fly away.")],
}
KNOWLEDGE_ORDER = ["bear", "alpha", "lawyer", "transformation", "law", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the words "{f["bear"].label_word}", "{f["alpha"].label_word}", and "{f["lawyer"].label_word}".',
        f"Tell a frontier story where a bear transforms into something larger and helps an alpha and a lawyer settle a hard problem.",
        "Write a tall tale with a transformation, a lawyer, and a bear that ends in a peaceful image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    bear, alpha, lawyer, place, problem, trans, response = (
        f["bear"], f["alpha"], f["lawyer"], f["place"], f["problem"], f["trans"], f["response"]
    )
    return [
        ("Who is the story about?", f"It is about a bear, an alpha, and a lawyer at {place.name}. The bear is the one who changes the most."),
        ("What problem were they facing?", f"They were facing {problem.label}. {problem.risk}"),
        ("What changed in the story?", f"The bear had a transformation and became {trans.form}. That made the bear big enough to help the others."),
        ("How did the lawyer help?", f"The lawyer {response.qa_text}. That gave the town a fair way forward."),
        ("How did the story end?", f"It ended with peace in the town and the bear standing huge in the last light. The ending image proves the transformation really happened."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["trans"].tags) | {"bear", "lawyer", "alpha"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this tall tale needs a real transformation, a lawyer's fairness, and a problem worth changing.)"


ASP_RULES = r"""
valid(P, R, T) :- place(P), problem(R), transformation(T), response(Resp), sense(Resp,S), S >= sense_min, pressure(R,Pr), Pr >= 1, size_gain(T,G), G >= 1.
grows(bear) :- wonder(bear), size_gain(T, G), G >= 3.
peaceful :- response(R), response_power(R,P), P >= 2.
outcome(peaceful) :- peaceful.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("pressure", pid, p.pressure))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("size_gain", tid, t.size_gain))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("response_power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos():")
        print(" only in python:", sorted(py - cl))
        print(" only in asp:", sorted(cl - py))
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print("SMOKE TEST FAILED:", exc)
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with bear, alpha, lawyer, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--response", choices=RESOLUTIONS)
    ap.add_argument("--bear-name")
    ap.add_argument("--alpha-name")
    ap.add_argument("--lawyer-name")
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
    if args.response and RESOLUTIONS[args.response].sense < 2:
        raise StoryError("(No story: the chosen response is too weak for this tall tale.)")
    p = args.place or rng.choice(list(PLACES))
    pr = args.problem or rng.choice(list(PROBLEMS))
    t = args.transformation or rng.choice(list(TRANSFORMATIONS))
    r = args.response or rng.choice(list(RESOLUTIONS))
    bear_name = args.bear_name or rng.choice(["Bear", "Bruno", "Bram", "Blue Bear"])
    alpha_name = args.alpha_name or rng.choice(["Alpha", "Alder", "Asher", "Arrow"])
    lawyer_name = args.lawyer_name or rng.choice(["Lawyer Lucy", "Lawyer Lou", "Lawyer Lane", "Lawyer June"])
    return StoryParams(p, pr, t, r, bear_name, alpha_name, lawyer_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], TRANSFORMATIONS[params.transformation],
                 RESOLUTIONS[params.response], params.bear_name, params.alpha_name, params.lawyer_name)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(p, pr, t, "bridge", "Bear", "Alpha", "Lawyer Lane")) for p, pr, t in valid_combos()[:5]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
