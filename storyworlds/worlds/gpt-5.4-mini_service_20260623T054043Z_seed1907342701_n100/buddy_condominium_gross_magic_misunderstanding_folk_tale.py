#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/buddy_condominium_gross_magic_misunderstanding_folk_tale.py
==============================================================================================================

A standalone storyworld for a folk-tale flavored condominium tale of magic,
misunderstanding, and a gross little mess that gets understood in time.

The seed idea:
A buddy in a condominium finds a "magic" answer to a problem, but the spell is
misunderstood and turns something gross. A helpful grown-up or neighbor helps
set it right, and the ending proves what changed in the room.

This world keeps the story small and concrete:
- one child-like lead ("buddy") with a helper
- one condominium setting
- one magical misunderstanding
- one gross physical consequence
- one sensible fix that clears the mess

It follows the shared storyworld contract:
- StoryParams, build_parser, resolve_params, generate, emit, main
- eagerly imports storyworlds/results.py
- lazily imports storyworlds/asp.py in ASP helpers
- provides Python valid-combo reasoning and an ASP twin
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, --seed, -n
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    helper: bool = False
    place: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    key: str
    label: str
    mood: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    key: str
    label: str
    verb: str
    gross: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicThing:
    key: str
    label: str
    phrase: str
    effect: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    key: str
    label: str
    phrase: str
    method: str
    power: int
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_gross(world: World) -> list[str]:
    out: list[str] = []
    lead = world.facts["lead"]
    problem = world.facts["problem"]
    if lead.meters.get(problem.key, 0.0) < THRESHOLD:
        return out
    sig = ("gross", lead.id, problem.key)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lead.meters["gross"] = 1.0
    lead.memes["embarrassed"] += 1
    world.get("mess").meters["gross"] = 1.0
    out.append(f"That turned the floor {problem.gross}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    lead = world.facts["lead"]
    helper = world.facts["helper"]
    if lead.meters.get("gross", 0.0) < THRESHOLD:
        return out
    sig = ("worry", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["worry"] += 1
    out.append(f"{helper.label} saw the mess and frowned.")
    return out


CAUSAL_RULES = [
    Rule("gross", "physical", _r_gross),
    Rule("worry", "social", _r_worry),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_at_risk(place: Place, problem: Problem, magic: MagicThing) -> bool:
    return problem.key in magic.needs and place.key in PLACE_KEYS and problem.key in PROBLEM_KEYS


def can_fix(problem: Problem, fix: Fix) -> bool:
    return problem.key in fix.tags and fix.power >= 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES.values():
        for prob in PROBLEMS.values():
            for mag in MAGICS.values():
                for fx in FIXES.values():
                    if p.key in {"hall", "stairs", "lobby", "garden"} and prob.key in mag.needs and can_fix(prob, fx):
                        combos.append((p.key, prob.key, mag.key, fx.key))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    magic: str
    fix: str
    lead_name: str = "Buddy"
    lead_type: str = "boy"
    helper_name: str = "Mabel"
    helper_type: str = "woman"
    seed: Optional[int] = None


PLACES = {
    "lobby": Place("lobby", "the condominium lobby", "marble-smooth", {"slip", "spark", "smear"}),
    "hall": Place("hall", "the long hallway", "echoing", {"slip", "spark", "smear"}),
    "laundry": Place("laundry", "the laundry room", "warm and steamy", {"stain", "spark", "smear"}),
    "rooftop": Place("rooftop", "the rooftop garden", "windy and bright", {"sprout", "spark", "smear"}),
}
PLACE_KEYS = set(PLACES)

PROBLEMS = {
    "slip": Problem("slip", "a slippery puddle", "mop", "gross", "slimy", {"wet", "gross"}),
    "stain": Problem("stain", "a sticky stain", "wipe", "gross", "smeary", {"sticky", "gross"}),
    "spark": Problem("spark", "a tiny sparkly spill", "dust", "gross", "shimmery", {"magic", "gross"}),
}
PROBLEM_KEYS = set(PROBLEMS)

MAGICS = {
    "broomspell": MagicThing("broomspell", "a broom spell", "the broom spell", "swept with a whoosh", {"spark", "stain", "slip"}, {"magic"}),
    "soapspell": MagicThing("soapspell", "a soap spell", "the soap spell", "foamed into shiny bubbles", {"stain", "slip"}, {"magic"}),
    "glowspell": MagicThing("glowspell", "a glow spell", "the glow spell", "glimmered like moonlight", {"spark", "stain"}, {"magic"}),
}
FIXES = {
    "mop": Fix("mop", "a mop and bucket", "the mop and bucket", "mopped until the shine came back", 2, {"slip"}),
    "cloth": Fix("cloth", "a clean cloth", "the clean cloth", "wiped the spot clear", 2, {"stain", "spark"}),
    "soap": Fix("soap", "a bowl of soap water", "the soap water", "washed the floor fresh", 2, {"stain", "slip"}),
}


def _story_names(rng: random.Random) -> tuple[str, str, str, str]:
    lead_name = rng.choice(["Buddy", "Pip", "Milo", "Nina", "Lila", "Hugo"])
    helper_name = rng.choice([n for n in ["Mabel", "Gwen", "Anya", "Tomas", "Uncle Ben", "Aunt Dot"] if n != lead_name])
    lead_type = rng.choice(["boy", "girl"])
    helper_type = rng.choice(["woman", "man"])
    return lead_name, lead_type, helper_name, helper_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.magic is None or c[2] == args.magic)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, magic, fix = rng.choice(sorted(combos))
    lead_name, lead_type, helper_name, helper_type = _story_names(rng)
    return StoryParams(place=place, problem=problem, magic=magic, fix=fix,
                       lead_name=lead_name, lead_type=lead_type,
                       helper_name=helper_name, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.magic not in MAGICS or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    magic = MAGICS[params.magic]
    fix = FIXES[params.fix]
    if problem.key not in magic.needs or not can_fix(problem, fix):
        raise StoryError("This magic and fix do not make a reasonable story.")

    world = World(place)
    lead = world.add(Entity(id="lead", kind="character", type=params.lead_type, label=params.lead_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    mess = world.add(Entity(id="mess", label=problem.label, type="thing"))
    lead.meters.update({problem.key: 0.0, "gross": 0.0})
    lead.memes.update({"curious": 1.0, "joy": 1.0, "embarrassed": 0.0})
    helper.meters.update({"gross": 0.0})
    helper.memes.update({"worry": 0.0, "kindness": 1.0})
    mess.meters.update({"gross": 0.0})
    world.facts.update(lead=lead, helper=helper, place=place, problem=problem, magic=magic, fix=fix, mess=mess)

    world.say(f"Once in {place.label}, {lead.label} and {helper.label} were a buddy pair with a small errand to do.")
    world.say(f"They had heard of {magic.phrase}, because in a folk tale even a hallway may hide a little magic.")
    world.para()
    world.say(f"Near the {problem.label}, {lead.label} tried {magic.effect} to {problem.verb} the trouble away.")
    lead.meters[problem.key] = 1.0
    lead.memes["curious"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{helper.label} said, 'Oh dear, that looked {problem.clue}, but it was only a misunderstanding.'")
    helper.memes["worry"] += 1
    world.say(f"Together they used {fix.phrase}, and {fix.method}.")
    lead.meters["gross"] = 0.0
    helper.meters["gross"] = 0.0
    world.get("mess").meters["gross"] = 0.0
    world.para()
    world.say(f"In the end, the {problem.label} was gone, the floor was clean, and the condominium smelled fresh again.")
    world.say(f"{lead.label} and {helper.label} left the place shining, as if the magic had been kindly understood at last.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story about {f["lead"].label}, a buddy in {f["place"].label}, where {f["magic"].label} causes a gross misunderstanding.',
        f"Tell a gentle condominium story where {f['lead'].label} uses {f['magic'].label} on {f['problem'].label}, but the mistake is only temporary.",
        f'Write a short magic-and-misunderstanding tale that includes the words "buddy", "condominium", and "gross".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    place = f["place"]
    problem = f["problem"]
    magic = f["magic"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What did {lead.label} try to do in {place.label}?",
            answer=f"{lead.label} tried to use {magic.label} to {problem.verb} away the trouble. It seemed clever at first, but it became a misunderstanding when the result turned {problem.gross}.",
        ),
        QAItem(
            question=f"Why did the floor become gross?",
            answer=f"It became gross because the magic was used on {problem.label}, and that brought out a messy change instead of a clean one. {helper.label} noticed the mistake and helped put things right.",
        ),
        QAItem(
            question=f"How did {lead.label} and {helper.label} fix the problem?",
            answer=f"They used {fix.label} and its {fix.method} to clear the mess. That worked because the fix fit the kind of trouble they had found.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {problem.label} was gone and the condominium smelled fresh again. The story ends with a clean floor, showing the misunderstanding had been resolved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condominium?",
            answer="A condominium is a home in a building where people live in separate apartments and share some common spaces.",
        ),
        QAItem(
            question="What does gross mean?",
            answer="Gross means dirty, sticky, smelly, or unpleasant to look at.",
        ),
        QAItem(
            question="Why can magic be misunderstood in a story?",
            answer="Magic can be misunderstood when someone expects one result, but the spell does something different. That is a common folk-tale problem because wishes do not always work the way people imagine.",
        ),
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lobby", problem="slip", magic="soapspell", fix="soap", lead_name="Buddy", lead_type="boy", helper_name="Mabel", helper_type="woman"),
    StoryParams(place="hall", problem="stain", magic="broomspell", fix="cloth", lead_name="Pip", lead_type="girl", helper_name="Aunt Dot", helper_type="woman"),
    StoryParams(place="laundry", problem="spark", magic="glowspell", fix="cloth", lead_name="Milo", lead_type="boy", helper_name="Uncle Ben", helper_type="man"),
    StoryParams(place="rooftop", problem="slip", magic="soapspell", fix="mop", lead_name="Nina", lead_type="girl", helper_name="Gwen", helper_type="woman"),
]


ASP_RULES = r"""
at_risk(P, Prob, Mag) :- place(P), problem(Prob), magic(Mag), needs(Mag, Prob).
can_fix(Prob, Fix) :- problem(Prob), fix(Fix), fixes(Fix, Prob).
valid(P, Prob, Mag, Fix) :- at_risk(P, Prob, Mag), can_fix(Prob, Fix).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
    for pr in PROBLEMS.values():
        lines.append(asp.fact("problem", pr.key))
    for m in MAGICS.values():
        lines.append(asp.fact("magic", m.key))
        for need in sorted(m.needs):
            lines.append(asp.fact("needs", m.key, need))
    for fx in FIXES.values():
        lines.append(asp.fact("fix", fx.key))
        for tag in sorted(fx.tags):
            lines.append(asp.fact("fixes", fx.key, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP valid-combo reasoning.")
        print(" only python:", sorted(py - cl))
        print(" only clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, magic=None, fix=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: valid-combo parity and smoke test passed ({len(py)} combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale condominium storyworld with magic and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.problem is None or c[1] == args.problem)
              and (args.magic is None or c[2] == args.magic)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, magic, fix = rng.choice(sorted(combos))
    lead_name, lead_type = rng.choice([("Buddy", "boy"), ("Pip", "girl"), ("Milo", "boy"), ("Nina", "girl")])
    helper_name, helper_type = rng.choice([("Mabel", "woman"), ("Aunt Dot", "woman"), ("Uncle Ben", "man"), ("Gwen", "woman")])
    return StoryParams(place=place, problem=problem, magic=magic, fix=fix,
                       lead_name=lead_name, lead_type=lead_type,
                       helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, magic, fix) combos:\n")
        for row in combos:
            print("  ", row)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.lead_name}: {p.magic} at {p.place} ({p.problem} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
