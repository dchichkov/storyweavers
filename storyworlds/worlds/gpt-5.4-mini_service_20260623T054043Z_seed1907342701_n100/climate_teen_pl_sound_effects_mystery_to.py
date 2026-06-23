#!/usr/bin/env python3
"""
storyworlds/worlds/climate_teen_pl_sound_effects_mystery_to.py
==============================================================

A standalone story world for a tiny whodunit about a climate-club mystery:
a teen-pl group hears strange sound effects, investigates clues in the weather,
and solves what is really causing the odd shift in the school's climate report.

Seed-inspired premise:
- Words to include: climate, teen-pl
- Features: Sound Effects, Mystery to Solve
- Style: Whodunit

The world is deliberately small:
- 4 to 6 valid story combos
- one mystery setup, one clue chain, one reveal, one ending image
- typed entities with physical meters and emotional memes
- a causal rule engine plus an inline ASP twin
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    held_by: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    sound: str
    cause: str
    clue: str
    climate_detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    hidden_cause: str
    obvious_sound: str
    mess: str
    evidence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    action: str
    reveal: str
    solves: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    method: str
    teen_name: str
    teen_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_revealed"):
        return out
    culprit = world.facts["problem_cfg"].hidden_cause
    signal = world.facts["problem_cfg"].obvious_sound
    if culprit and signal and ("clue", culprit) not in world.fired:
        world.fired.add(("clue", culprit))
        world.facts["clue_seen"] = True
        out.append("__clue__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("clue_seen"):
        return out
    if world.facts.get("mystery_revealed"):
        return out
    method = world.facts["method_cfg"]
    if method.id == "follow_the_echo" and ("solve", method.id) not in world.fired:
        world.fired.add(("solve", method.id))
        world.facts["mystery_revealed"] = True
        out.append("__solve__")
    return out


CAUSAL_RULES = [
    Rule("clue", "mystery", _r_clue),
    Rule("solve", "mystery", _r_solve),
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
            if s == "__clue__":
                world.say(f"A sharp sound hid a clue in the climate lab.")
            elif s == "__solve__":
                world.say(f"The clue pointed straight to the answer.")
    return produced


def mystery_at_risk(problem: Problem, place: Place) -> bool:
    return problem.id in place.affords


def solve_possible(method: Method, problem: Problem, place: Place) -> bool:
    return mystery_at_risk(problem, place) and method.solves == problem.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for pr in PROBLEMS:
            for m in METHODS:
                if mystery_at_risk(PROBLEMS[pr], PLACES[p]) and solve_possible(METHODS[m], PROBLEMS[pr], PLACES[p]):
                    combos.append((p, pr, m))
    return combos


def sound_sentence(place: Place, problem: Problem) -> str:
    return f"{place.sound} {problem.obvious_sound}".strip()


def clue_sentence(place: Place, problem: Problem) -> str:
    return f"{place.climate_detail} gave the clue a shape."


def setup_story(world: World, teen: Entity, helper: Entity, problem: Problem) -> None:
    teen.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On the first warm morning of the week, {teen.id} and {helper.id} met at {world.place.label} "
        f"for the teen-pl climate club."
    )
    world.say(
        f"They heard {sound_sentence(world.place, problem)}, and the noise made the room feel like a mystery."
    )
    world.say(
        f"{clue_sentence(world.place, problem)}"
    )


def investigate(world: World, teen: Entity, helper: Entity, method: Method) -> None:
    teen.memes["worry"] += 1
    world.say(
        f"{teen.id} frowned and said, \"That does not sound right.\" {helper.id} nodded and asked them to listen again."
    )
    world.say(
        f"Together they used {method.label}, and the little sound led them past the maps and gauges."
    )


def reveal(world: World, teen: Entity, helper: Entity, problem: Problem, method: Method) -> None:
    world.facts["mystery_revealed"] = True
    world.say(
        f"At last, they found {problem.hidden_cause}, and the strange noise made sense."
    )
    world.say(
        f"It was really {method.reveal}, not a broken climate machine at all."
    )


def ending(world: World, teen: Entity, helper: Entity, method: Method) -> None:
    teen.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the end, the climate chart was quiet again, and {teen.id} taped it to the wall with a smile."
    )
    world.say(
        f"{helper.id} clicked the last button, and the room settled into a calm little hum."
    )
    world.say(
        f"The teen-pl club left the lab with clean notes, bright faces, and one solved mystery."
    )


def tell(place: Place, problem: Problem, method: Method,
         teen_name: str, teen_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    teen = world.add(Entity(id=teen_name, kind="character", type=teen_type, role="detective", tags={"teen-pl"}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    clue_box = world.add(Entity(id="clue_box", label="the climate chart", type="thing"))
    world.facts = {
        "teen": teen,
        "helper": helper,
        "clue_box": clue_box,
        "place_cfg": place,
        "problem_cfg": problem,
        "method_cfg": method,
        "mystery_revealed": False,
        "clue_seen": False,
    }
    setup_story(world, teen, helper, problem)
    world.para()
    investigate(world, teen, helper, method)
    propagate(world, narrate=True)
    world.para()
    reveal(world, teen, helper, problem, method)
    world.para()
    ending(world, teen, helper, method)
    return world


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="the greenhouse",
        sound="tap-tap",
        cause="a dripping hose",
        clue="a wet trail",
        climate_detail="Warm air fogged the glass",
        affords={"dripping_hose"},
    ),
    "rooftop": Place(
        id="rooftop",
        label="the rooftop lab",
        sound="whirr-whirr",
        cause="a loose fan",
        clue="a tiny fan shadow",
        climate_detail="A windy roof pushed the papers in little waves",
        affords={"loose_fan"},
    ),
    "library": Place(
        id="library",
        label="the school library",
        sound="rustle-rustle",
        cause="a hidden vent",
        clue="a strip of cool air",
        climate_detail="The shelves kept the air still and cool",
        affords={"hidden_vent"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        sound="drip-drip",
        cause="a tilted rain barrel",
        clue="a shining puddle",
        climate_detail="Clouds had left the stones damp and silver",
        affords={"tilted_barrel"},
    ),
}

PROBLEMS = {
    "dripping_hose": Problem(
        id="dripping_hose",
        label="a dripping hose",
        hidden_cause="the hose behind the fern",
        obvious_sound="tap-tap",
        mess="wet leaves",
        evidence="wet trail",
        tags={"water", "climate"},
    ),
    "loose_fan": Problem(
        id="loose_fan",
        label="a loose fan",
        hidden_cause="the ceiling fan clip",
        obvious_sound="whirr-whirr",
        mess="bent papers",
        evidence="fan shadow",
        tags={"air", "climate"},
    ),
    "hidden_vent": Problem(
        id="hidden_vent",
        label="a hidden vent",
        hidden_cause="the back vent grille",
        obvious_sound="rustle-rustle",
        mess="cool drafts",
        evidence="cool air",
        tags={"air", "climate"},
    ),
    "tilted_barrel": Problem(
        id="tilted_barrel",
        label="a tilted rain barrel",
        hidden_cause="the barrel spout",
        obvious_sound="drip-drip",
        mess="muddy shoes",
        evidence="puddle",
        tags={"water", "climate"},
    ),
}

METHODS = {
    "follow_the_echo": Method(
        id="follow_the_echo",
        label="the echo map",
        action="follow the echo",
        reveal="the echo was bouncing off the hose, not a machine",
        solves="dripping_hose",
        tags={"sound", "clue"},
    ),
    "check_the_fan": Method(
        id="check_the_fan",
        label="a ladder and a flashlight",
        action="check the fan",
        reveal="the noise came from the loose fan blade",
        solves="loose_fan",
        tags={"sound", "clue"},
    ),
    "lift_the_grate": Method(
        id="lift_the_grate",
        label="a flashlight and gloves",
        action="lift the grate",
        reveal="the draft came from the hidden vent",
        solves="hidden_vent",
        tags={"sound", "clue"},
    ),
    "straighten_barrel": Method(
        id="straighten_barrel",
        label="a wrench and a bucket",
        action="straighten the barrel",
        reveal="the drip came from the tilted barrel spout",
        solves="tilted_barrel",
        tags={"sound", "clue"},
    ),
}


def valid_story_rows() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(place="greenhouse", problem="dripping_hose", method="follow_the_echo", teen_name="Maya", teen_type="girl", helper_name="Noah", helper_type="boy"),
    StoryParams(place="rooftop", problem="loose_fan", method="check_the_fan", teen_name="Iris", teen_type="girl", helper_name="Ben", helper_type="boy"),
    StoryParams(place="library", problem="hidden_vent", method="lift_the_grate", teen_name="Leo", teen_type="boy", helper_name="Ava", helper_type="girl"),
    StoryParams(place="courtyard", problem="tilted_barrel", method="straighten_barrel", teen_name="Zoe", teen_type="girl", helper_name="Eli", helper_type="boy"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teen, helper, place_cfg, problem_cfg, method_cfg = f["teen"], f["helper"], f["place_cfg"], f["problem_cfg"], f["method_cfg"]
    return [
        f'Write a whodunit for a child that uses the words "climate" and "teen-pl" and includes a mysterious sound in {place_cfg.label}.',
        f"Tell a short mystery where {teen.id} and {helper.id} hear {problem_cfg.obvious_sound} at {place_cfg.label} and solve it by using {method_cfg.label}.",
        f"Write a gentle detective story about the teen-pl climate club, a strange noise, and the real cause hiding behind the clues.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    teen, helper, place_cfg, problem_cfg, method_cfg = f["teen"], f["helper"], f["place_cfg"], f["problem_cfg"], f["method_cfg"]
    return [
        QAItem(
            question=f"Who solved the mystery in {place_cfg.label}?",
            answer=f"{teen.id} and {helper.id} solved it together. They listened carefully, followed the clues, and found the real cause.",
        ),
        QAItem(
            question=f"What strange sound did they hear at {place_cfg.label}?",
            answer=f"They heard {problem_cfg.obvious_sound}. It sounded odd enough to turn the climate club meeting into a mystery.",
        ),
        QAItem(
            question=f"How did {teen.id} find the answer?",
            answer=f"{teen.id} used {method_cfg.label} with {helper.id}. That helped them trace the sound back to {problem_cfg.hidden_cause}.",
        ),
        QAItem(
            question=f"Why was the climate room calm again at the end?",
            answer=f"The hidden cause was fixed, so the noise stopped. After that, the charts and papers could rest quietly again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is climate?",
            answer="Climate means the usual kind of weather a place has over a long time. People talk about climate when they want to understand heat, rain, wind, and change.",
        ),
        QAItem(
            question="What does a detective do in a mystery?",
            answer="A detective looks for clues, asks careful questions, and puts the pieces together. That is how a mystery gets solved.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you imagine a noise, like tap-tap or whirr-whirr. They make the scene feel lively and real.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: that combination does not fit the mystery well enough.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about climate-club mysteries.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--teen-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
              and (args.problem is None or c[1] == args.problem)
              and (args.method is None or c[2] == args.method)]
    if not combos:
        raise StoryError(explain_rejection())
    place, problem, method = rng.choice(sorted(combos))
    teen_type = args.teen_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if teen_type == "girl" else "girl")
    teen_name = args.name or rng.choice(["Maya", "Iris", "Leo", "Zoe", "Nina", "Ari", "Tess", "Eli"])
    helper_name = args.helper_name or rng.choice([n for n in ["Noah", "Ben", "Ava", "Liam", "Mina", "June", "Kai", "Luz"] if n != teen_name])
    return StoryParams(place=place, problem=problem, method=method, teen_name=teen_name, teen_type=teen_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.method not in METHODS:
        raise StoryError(explain_rejection())
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]
    if not solve_possible(method, problem, place):
        raise StoryError(explain_rejection())
    world = tell(place, problem, method, params.teen_name, params.teen_type, params.helper_name, params.helper_type)
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


ASP_RULES = r"""
valid(P, R, M) :- place(P), problem(R), method(M), solves(M, R), afford(P, R).
mystery_revealed(P, R) :- valid(P, R, M), method(M), solves(M, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for p in place.affords:
            lines.append(asp.fact("afford", pid, p))
    for rid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", rid))
        lines.append(asp.fact("solved_by_sound", rid, prob.obvious_sound))
    for mid, meth in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("solves", mid, meth.solves))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    try:
        python_set = set(valid_combos())
        clingo_set = set(asp_valid_combos())
        if python_set != clingo_set:
            print("MISMATCH in valid combos")
            print("only python:", sorted(python_set - clingo_set))
            print("only clingo:", sorted(clingo_set - python_set))
            return 1
        params = resolve_params(argparse.Namespace(place=None, problem=None, method=None, name=None, helper_name=None, teen_type=None, helper_type=None), random.Random(777))
        sample = generate(params)
        _ = sample.story
        print(f"OK: {len(python_set)} valid combos; generate() smoke test passed.")
        return 0
    except Exception:
        traceback.print_exc()
        return 1


CURATED = [
    StoryParams(place="greenhouse", problem="dripping_hose", method="follow_the_echo", teen_name="Maya", teen_type="girl", helper_name="Noah", helper_type="boy"),
    StoryParams(place="rooftop", problem="loose_fan", method="check_the_fan", teen_name="Iris", teen_type="girl", helper_name="Ben", helper_type="boy"),
    StoryParams(place="library", problem="hidden_vent", method="lift_the_grate", teen_name="Leo", teen_type="boy", helper_name="Ava", helper_type="girl"),
    StoryParams(place="courtyard", problem="tilted_barrel", method="straighten_barrel", teen_name="Zoe", teen_type="girl", helper_name="Eli", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
