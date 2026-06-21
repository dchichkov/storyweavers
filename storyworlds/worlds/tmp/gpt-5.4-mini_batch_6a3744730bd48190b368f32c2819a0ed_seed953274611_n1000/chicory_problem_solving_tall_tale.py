#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chicory_problem_solving_tall_tale.py
=====================================================================

A standalone storyworld for a tall-tale style problem-solving story about
chicory.

Premise:
- A child or small crew is trying to make something work in a funny, outsized
  little world.
- Chicory is the important material: it can be roasted, brewed, or used to
  fix a stubborn problem.
- The story should have a clear problem, a clever turn, and a cheerful ending
  image that proves the fix worked.

The world is small, physical, and state-driven:
- typed entities have physical meters and emotional memes
- the story is assembled from simulation, not by swapping nouns in a frozen
  paragraph
- the rendered prose stays child-facing and tall-tale flavored

This script follows the Storyweavers world contract:
- stdlib only
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
MOOD_GOOD = 1.0


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
    edible: bool = False
    brewable: bool = False
    fixable: bool = False
    special: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    place: str = "the prairie kitchen"
    problem: str = "thin_soup"
    chicory: str = "roasted_chicory"
    fix: str = "thicken"
    helper: str = "Mina"
    helper_gender: str = "girl"
    elder: str = "Aunt Juniper"
    elder_gender: str = "woman"
    seed: Optional[int] = None


@dataclass
class PlaceDef:
    id: str
    scene: str
    opening: str
    problem_line: str
    problem_detail: str
    tail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemDef:
    id: str
    label: str
    symptom: str
    cause: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ChicoryDef:
    id: str
    label: str
    phrase: str
    use: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixDef:
    id: str
    label: str
    action: str
    result: str
    power: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    if pot.meters["spill"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("kitchen").meters["mess"] += 1
    world.get("helper").memes["worry"] += 1
    out.append("__spill__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").memes["calm"] < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("helper").memes["hope"] += 1
    out.append("__settle__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("settle", _r_settle)]


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


def problem_is_reasonable(problem: ProblemDef, chicory: ChicoryDef, fix: FixDef) -> bool:
    return problem.id in PROBLEM_FIX_MAP and fix.id in PROBLEM_FIX_MAP[problem.id] and chicory.id in CHICORY_USE_MAP


def best_fix(problem_id: str) -> FixDef:
    return max(PROBLEM_FIX_MAP[problem_id], key=lambda f: f.power)


def can_solve(problem: ProblemDef, fix: FixDef) -> bool:
    return fix.power >= problem.severity


def predict(world: World, fix: FixDef) -> dict:
    sim = world.copy()
    sim.get("helper").memes["calm"] += 1
    if can_solve(PROBLEMS[sim.facts["problem"].id], fix):
        sim.get("pot").meters["fixed"] += 1
    return {"fixed": sim.get("pot").meters["fixed"] >= THRESHOLD}


def setup(world: World, place: PlaceDef, helper: Entity, elder: Entity) -> None:
    helper.memes["curiosity"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"On a day so broad it looked like the sky had borrowed a pair of overalls, "
        f"{helper.id} and {elder.label_word} worked in {place.scene}."
    )
    world.say(place.opening)


def introduce_problem(world: World, place: PlaceDef, problem: ProblemDef) -> None:
    world.say(
        f"But there was trouble in the pot: {problem.symptom}. {place.problem_line} "
        f"{place.problem_detail}"
    )


def try_small_fixes(world: World, helper: Entity, problem: ProblemDef, chicory: ChicoryDef) -> None:
    helper.memes["frustration"] += 1
    world.say(
        f"{helper.id} tried one tiny fix after another, but the problem kept its boots on. "
        f"Even a prairie wind seemed to say, '{problem.cause}.'"
    )
    world.say(
        f"Then {helper.id} sniffed {chicory.phrase}. {helper.pronoun().capitalize()} said it "
        f"smelled {chicory.smell} and might be just the thing."
    )


def ask_elder(world: World, helper: Entity, elder: Entity, chicory: ChicoryDef) -> None:
    elder.memes["patient"] += 1
    world.say(
        f'{helper.id} asked, "Could {chicory.label_word} help?" '
        f"{elder.label_word} nodded as if the answer had been waiting in the skillet."
    )


def apply_fix(world: World, helper: Entity, elder: Entity, problem: ProblemDef,
              chicory: ChicoryDef, fix: FixDef) -> None:
    helper.memes["calm"] += 1
    helper.memes["frustration"] = 0.0
    world.get("pot").meters["fixed"] += 1
    world.say(
        f"{elder.label_word} told {helper.id} to {fix.action}. "
        f"Together they used {chicory.phrase}; {fix.result}."
    )
    world.say(
        f"The kitchen quieted down. The spoon stood up straight again, the steam rose "
        f"soft and proud, and the little trouble was no trouble at all."
    )


def ending(world: World, helper: Entity, elder: Entity, place: PlaceDef, problem: ProblemDef,
           chicory: ChicoryDef) -> None:
    helper.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"In the end, {helper.id} gave a grin wide enough to hang moonlight on. "
        f"{place.tail} {helper.id} kept the pot steady, and the chicory made the whole "
        f"house smell like a wise old wagon with cookies in its pockets."
    )


def tell(place: PlaceDef, problem: ProblemDef, chicory: ChicoryDef, fix: FixDef,
         helper_name: str = "Mina", helper_gender: str = "girl",
         elder_name: str = "Aunt Juniper", elder_gender: str = "woman") -> World:
    world = World()
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder", label=elder_name))
    kitchen = world.add(Entity(id="kitchen", type="room", label=place.scene))
    pot = world.add(Entity(id="pot", type="thing", label="the pot"))
    pot.meters["spill"] = 1.0 if problem.id == "thin_soup" else 0.0
    world.facts["place"] = place
    world.facts["problem"] = problem
    world.facts["chicory"] = chicory
    world.facts["fix"] = fix

    setup(world, place, helper, elder)
    world.para()
    introduce_problem(world, place, problem)
    try_small_fixes(world, helper, problem, chicory)
    ask_elder(world, helper, elder, chicory)
    world.para()
    apply_fix(world, helper, elder, problem, chicory, fix)
    ending(world, helper, elder, place, problem, chicory)
    propagate(world, narrate=False)
    world.facts.update(helper=helper, elder=elder, kitchen=kitchen, pot=pot)
    return world


PROBLEM_FIX_MAP = {
    "thin_soup": [],
    "stubborn_wagon": [],
    "foggy_lantern": [],
}
CHICORY_USE_MAP = {
    "roasted_chicory": "thicken",
    "chicory_coffee": "wake",
    "chicory_wick": "brighten",
}

PLACE_REGISTRY = {
    "prairie_kitchen": PlaceDef(
        id="prairie_kitchen",
        scene="the prairie kitchen",
        opening="A copper pot sat on the stove like a shiny moon in a hurry.",
        problem_line="The soup was so thin it could run through a wagon wheel.",
        problem_detail="If they served it now, the spoon would come out wearing only regret.",
        tail="By supper time",
        tags={"kitchen", "soup"},
    ),
    "wagon_camp": PlaceDef(
        id="wagon_camp",
        scene="the wagon camp",
        opening="A campfire cracked and popped, while the pots hung like sleepy bells.",
        problem_line="The wagon wheel had gone stubborn.",
        problem_detail="Every turn made a squeak fit for the age of dinosaurs.",
        tail="By sunset",
        tags={"wagon", "camp"},
    ),
    "lantern_shed": PlaceDef(
        id="lantern_shed",
        scene="the lantern shed",
        opening="The shed was full of lantern glass and dust that sparkled like ground stars.",
        problem_line="The lantern was foggy inside.",
        problem_detail="Its glow looked as weak as a firefly after a long nap.",
        tail="That night",
        tags={"lantern", "shed"},
    ),
}

PROBLEMS = {
    "thin_soup": ProblemDef(
        id="thin_soup",
        label="thin soup",
        symptom="the soup was as thin as a lark's whisper",
        cause="the broth needed something hearty and brown",
        severity=1,
        tags={"soup"},
    ),
    "stubborn_wagon": ProblemDef(
        id="stubborn_wagon",
        label="stubborn wagon wheel",
        symptom="the wagon wheel squeaked louder than a goose in a thunderstorm",
        cause="the axle needed a slick, clever fix",
        severity=2,
        tags={"wagon"},
    ),
    "foggy_lantern": ProblemDef(
        id="foggy_lantern",
        label="foggy lantern",
        symptom="the lantern glass was cloudy as a milk jug in rain",
        cause="the wick and glass needed a brightening spell of common sense",
        severity=2,
        tags={"lantern"},
    ),
}

CHICORY = {
    "roasted_chicory": ChicoryDef(
        id="roasted_chicory",
        label="chicory",
        phrase="a little jar of roasted chicory",
        use="thicken soup",
        smell="dark and toasty",
        tags={"chicory", "soup"},
    ),
    "chicory_coffee": ChicoryDef(
        id="chicory_coffee",
        label="chicory",
        phrase="a mug of chicory coffee",
        use="wake sleepy hands",
        smell="bold and brown",
        tags={"chicory", "coffee"},
    ),
    "chicory_wick": ChicoryDef(
        id="chicory_wick",
        label="chicory",
        phrase="a strip of dried chicory used as a wick",
        use="brighten a lantern",
        smell="earthy and sharp",
        tags={"chicory", "lantern"},
    ),
}

FIXES = {
    "thicken": FixDef(
        id="thicken",
        label="thicken the soup",
        action="stir in the chicory and simmer it slow",
        result="the soup grew rich and glossy, as if it had been told a good story",
        power=1,
        tags={"soup", "fix"},
    ),
    "tighten": FixDef(
        id="tighten",
        label="tighten the axle",
        action="grease the axle and tap the wheel true",
        result="the wagon wheel rolled smoother than a rabbit on ice",
        power=2,
        tags={"wagon", "fix"},
    ),
    "brighten": FixDef(
        id="brighten",
        label="brighten the lantern",
        action="clean the glass and feed the wick a better burn",
        result="the lantern glowed like a pocket sunrise",
        power=2,
        tags={"lantern", "fix"},
    ),
}

PROBLEM_FIX_MAP = {
    "thin_soup": [FIXES["thicken"]],
    "stubborn_wagon": [FIXES["tighten"]],
    "foggy_lantern": [FIXES["brighten"]],
}

CURATED = [
    StoryParams(place="the prairie kitchen", problem="thin_soup", chicory="roasted_chicory", fix="thicken", helper="Mina", helper_gender="girl", elder="Aunt Juniper", elder_gender="woman"),
    StoryParams(place="the wagon camp", problem="stubborn_wagon", chicory="chicory_coffee", fix="tighten", helper="Jeb", helper_gender="boy", elder="Uncle Sage", elder_gender="man"),
    StoryParams(place="the lantern shed", problem="foggy_lantern", chicory="chicory_wick", fix="brighten", helper="Lila", helper_gender="girl", elder="Grandma Blue", elder_gender="woman"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACE_REGISTRY.values():
        for prob in PROBLEMS.values():
            for ch in CHICORY.values():
                for fx in FIXES.values():
                    if problem_is_reasonable(prob, ch, fx):
                        combos.append((p.id, prob.id, ch.id))
    return sorted(set(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale problem solving with chicory.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--chicory", choices=CHICORY)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    if args.problem and args.fix:
        if args.fix not in {f.id for f in PROBLEM_FIX_MAP[args.problem]}:
            raise StoryError("That fix does not solve that problem in this little world.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.chicory is None or c[2] == args.chicory)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, chicory = rng.choice(combos)
    fix = args.fix or PROBLEM_FIX_MAP[problem][0].id
    helper = args.helper or rng.choice(["Mina", "Jeb", "Lila", "Toby", "Nell"])
    elder = args.elder or rng.choice(["Aunt Juniper", "Uncle Sage", "Grandma Blue"])
    helper_gender = "girl" if helper in {"Mina", "Lila", "Nell"} else "boy"
    elder_gender = "woman" if elder.startswith(("Aunt", "Grandma")) else "man"
    return StoryParams(place=place, problem=problem, chicory=chicory, fix=fix,
                       helper=helper, helper_gender=helper_gender,
                       elder=elder, elder_gender=elder_gender)


def story_text(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACE_REGISTRY or params.problem not in PROBLEMS or params.chicory not in CHICORY or params.fix not in FIXES:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(PLACE_REGISTRY[params.place], PROBLEMS[params.problem], CHICORY[params.chicory], FIXES[params.fix], params.helper, params.helper_gender, params.elder, params.elder_gender)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall-tale story for a child that includes the word chicory and ends with {f['place'].tail.lower()}.",
        f"Tell a problem-solving story where {f['helper'].id} uses chicory to fix {f['problem'].label}.",
        f"Write a funny, homespun story in which a youngster and a wise elder solve a stubborn problem with chicory.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper: Entity = f["helper"]
    elder: Entity = f["elder"]
    problem: ProblemDef = f["problem"]
    chicory: ChicoryDef = f["chicory"]
    fix: FixDef = f["fix"]
    return [
        ("What was the problem?", f"The problem was {problem.label}. It was stubborn enough to need a clever fix, not just a quick fuss."),
        ("What did they use?", f"They used {chicory.phrase}. The chicory gave them just the help they needed to solve the trouble."),
        ("How did they solve it?", f"They followed {elder.label_word}'s advice and {fix.action}. That turned the problem into a success."),
        ("How did the story end?", f"It ended with {helper.id} smiling as the job was done and the air smelled of chickory? No—the air smelled of chicory and the whole place felt steady again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is chicory?", answer="Chicory is a plant people can roast, brew, or use in clever old-time remedies. It has a dark, earthy smell and can help in little kitchen tricks."),
        QAItem(question="Why do tall tales sound so big?", answer="Tall tales make ordinary things sound larger than life. They turn small jobs into grand adventures without forgetting the ending."),
        QAItem(question="What does it mean to solve a problem?", answer="It means finding a way to make the trouble stop or work better. A good solution should fit the problem, not just look fancy."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_fix(thin_soup, thicken).
problem_fix(stubborn_wagon, tighten).
problem_fix(foggy_lantern, brighten).

valid(P, Prob, Chic) :- place(P), problem(Prob), chicory(Chic), problem_fix(Prob, _).
fix_ok(Prob, Fix) :- problem_fix(Prob, Fix).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for c in CHICORY:
        lines.append(asp.fact("chicory", c))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    for prob, fixes in PROBLEM_FIX_MAP.items():
        for fx in fixes:
            lines.append(asp.fact("problem_fix", prob, fx.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _pick_name(rng: random.Random) -> tuple[str, str]:
    if rng.random() < 0.5:
        return rng.choice(["Mina", "Lila", "Nell"]), "girl"
    return rng.choice(["Jeb", "Toby", "Will"]), "boy"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show fix_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale problem-solving story that includes "chicory" and takes place in {f["place"].scene}.',
        f"Tell a child-sized tall tale where {f['helper'].id} uses chicory to solve {f['problem'].label}.",
        f"Write a homespun adventure where a clever elder and a curious child fix a stubborn problem with chicory.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper: Entity = f["helper"]
    problem: ProblemDef = f["problem"]
    chicory: ChicoryDef = f["chicory"]
    fix: FixDef = f["fix"]
    elder: Entity = f["elder"]
    return [
        ("What was the trouble?", f"It was {problem.label}. The trouble was stubborn enough to need a real solution."),
        ("What did they use to help?", f"They used {chicory.phrase}. That gave them the edge they needed."),
        ("Who helped solve it?", f"{helper.id} and {elder.label_word} solved it together. The elder guided the fix and the child did the work."),
        ("How did it end?", f"It ended with the problem fixed and everyone feeling proud. The place looked steady again, which proved the solution worked."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is chicory used for in old-time cooking?", answer="People can roast chicory and use it to add a dark, earthy taste. In old stories, it is the kind of useful plant that helps when a problem needs a clever touch."),
        QAItem(question="What is a problem-solving story?", answer="It is a story where someone notices trouble, thinks carefully, and finds a way to fix it. The ending shows what changed because of the solution."),
        QAItem(question="What makes a tall tale feel like a tall tale?", answer="A tall tale uses big, lively language and makes everyday work sound grand. It usually has a funny, bold voice and a strong ending image."),
    ]


if __name__ == "__main__":
    main()
