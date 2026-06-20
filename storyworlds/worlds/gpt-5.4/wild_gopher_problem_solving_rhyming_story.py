#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wild_gopher_problem_solving_rhyming_story.py
=======================================================================

A standalone story world for a tiny "wild gopher problem solving" rhyming tale.

Premise
-------
A child in a garden or meadow is carrying or protecting something important when
a wild gopher's digging causes a practical problem: a wobble, spill risk, or
blocked path. A helper and a sensible tool let the child solve the problem in a
small, concrete way. The story is told in light rhyming prose, but the rhymes
still follow simulated state.

Model sketch
------------
Typed entities carry physical meters and emotional memes. The world tracks:

* a wild gopher digging loose earth or a hole,
* an at-risk task (watering, rolling, delivering seeds),
* a problem caused by the digging,
* a solution tool that actually fits that problem,
* a repaired ending that proves what changed.

Reasonableness
--------------
Not every tool fits every problem. A broom cannot safely bridge a hole, and a
board is not the right way to brush dirt off a path. The Python gate and inline
ASP twin agree on which combinations are valid.

Run it
------
    python storyworlds/worlds/gpt-5.4/wild_gopher_problem_solving_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/wild_gopher_problem_solving_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/wild_gopher_problem_solving_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4/wild_gopher_problem_solving_rhyming_story.py --verify
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

# Make shared helpers importable when run directly from this nested directory.
_THIS = os.path.abspath(__file__)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_THIS)))
sys.path.insert(0, _STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "gopher":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    ground: str
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    task: str
    item: str
    carry_phrase: str
    stumble_line: str
    risk_word: str
    fix_need: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    action: str
    trace: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    method_line: str
    ending_line: str
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hole_makes_trouble(world: World) -> list[str]:
    gopher = world.get("gopher")
    child = world.get("child")
    if gopher.meters["dug"] < THRESHOLD:
        return []
    sig = ("trouble", world.facts["problem"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["risk"] += 1
    child.memes["worry"] += 1
    return ["__problem__"]


def _r_solution_clears_risk(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["fixed"] < THRESHOLD:
        return []
    sig = ("clear_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["risk"] = 0.0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule("trouble", "physical", _r_hole_makes_trouble),
    Rule("clear_risk", "physical", _r_solution_clears_risk),
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


def fits(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for problem_id in PROBLEMS:
            for hazard_id in HAZARDS:
                for tool_id, tool in TOOLS.items():
                    if fits(PROBLEMS[problem_id], tool):
                        out.append((setting_id, problem_id, hazard_id, tool_id))
    return out


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not honestly solve the {problem.id} problem. "
        f"The fix must match the trouble in the ground, so pick a tool that can "
        f"{problem.fix_need}.)"
    )


def predict_problem(world: World) -> dict:
    sim = world.copy()
    gopher = sim.get("gopher")
    gopher.meters["dug"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "risk": child.meters["risk"],
        "worry": child.memes["worry"],
    }


def introduce(world: World, child: Entity, helper: Entity, setting: Setting,
              problem: Problem) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {setting.place}, beneath {setting.sky}, {child.id} skipped by with a swing and a song. "
        f"{helper.id} walked near, and the day felt bright and long."
    )
    world.say(
        f"{child.id} had {problem.carry_phrase}, snug and steady all along. "
        f'"I will {problem.task}," {child.pronoun()} hummed, "and nothing will go wrong."'
    )


def gopher_appears(world: World, gopher: Entity, hazard: Hazard, setting: Setting) -> None:
    gopher.memes["wild"] += 1
    world.say(
        f"Then out of the {setting.ground} popped a wild gopher, quick and small and strong. "
        f"{hazard.action.capitalize()}, {hazard.trace}, as if the earth had joined the song."
    )


def warn(world: World, helper: Entity, child: Entity, problem: Problem) -> None:
    pred = predict_problem(world)
    world.facts["predicted_risk"] = pred["risk"]
    child.memes["attention"] += 1
    world.say(
        f'{helper.id} pointed down. "Slow feet, sweet pea. {problem.stumble_line}" '
        f'{helper.pronoun()} said. "Let us look, think, and make it right instead."'
    )


def trouble(world: World, child: Entity, problem: Problem) -> None:
    gopher = world.get("gopher")
    gopher.meters["dug"] += 1
    child.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{problem.effect.capitalize()} and {problem.risk_word} danced close by. "
        f"{child.id} gave a tiny gasp and held {child.pronoun('possessive')} {problem.item} high."
    )


def think(world: World, child: Entity, helper: Entity, tool: Tool, problem: Problem) -> None:
    child.memes["thinking"] += 1
    helper.memes["thinking"] += 1
    world.say(
        f'"A rush would make a bigger mess; a plan is what we need," said {helper.id}. '
        f'"What can help us {problem.fix_need} with care and with good speed?"'
    )
    world.say(
        f'{child.id} looked, then nodded at {tool.phrase}. '
        f'"That can help," {child.pronoun()} said. "Let\'s use our eyes before our feet; '
        f'let thinking lead our tread."'
    )


def solve(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.meters["fixed"] += 1
    child.meters["wobble"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{tool.method_line} {helper.id} helped with calm and steady cheer; "
        f"the muddled path grew safe again, and the answer felt quite clear."
    )


def ending(world: World, child: Entity, gopher: Entity, tool: Tool, problem: Problem) -> None:
    child.memes["joy"] += 1
    child.memes["gratitude"] += 1
    world.say(
        f"{tool.ending_line} {child.id} could {problem.task} at last, light-hearted, proud, and bright. "
        f"Even the wild gopher blinked, then bobbed and slipped from sight."
    )
    world.say(
        f'So {child.id} learned a simple tune: "When trouble taps the door, '
        f'look low, think slow, use the right tool well, and fear will grow no more."'
    )


def tell(setting: Setting, problem: Problem, hazard: Hazard, tool: Tool,
         child_name: str = "Nell", child_type: str = "girl",
         helper_name: str = "Mom", helper_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    gopher = world.add(Entity(id="gopher", kind="animal", type="gopher", label="wild gopher"))
    world.facts.update(setting=setting, problem=problem, hazard=hazard, tool=tool)

    introduce(world, child, helper, setting, problem)
    world.para()
    gopher_appears(world, gopher, hazard, setting)
    warn(world, helper, child, problem)
    trouble(world, child, problem)
    world.para()
    think(world, child, helper, tool, problem)
    solve(world, child, helper, tool)
    world.para()
    ending(world, child, gopher, tool, problem)

    world.facts.update(
        child=child,
        helper=helper,
        gopher=gopher,
        solved=child.meters["fixed"] >= THRESHOLD,
        risked=world.facts.get("predicted_risk", 0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "meadow": Setting("meadow", "a windy meadow", "soft grass", "a butter-yellow sky",
                      tags={"meadow", "outside"}),
    "garden": Setting("garden", "a sunny garden", "crumbly garden dirt", "a blue and breezy sky",
                      tags={"garden", "outside"}),
    "orchard": Setting("orchard", "a little orchard path", "leafy earth", "a warm gold sky",
                       tags={"orchard", "outside"}),
}

PROBLEMS = {
    "watering": Problem(
        "watering",
        "water the thirsty rows",
        "watering can",
        "a round watering can with a silver spout",
        "The ground is bumpy now. You may tip the can and spill the flow.",
        "spill",
        "cross the bumpy spot",
        "The can began to wobble as the child stepped to and fro",
        tags={"water", "garden"}
    ),
    "wagon": Problem(
        "wagon",
        "roll the berry wagon home",
        "little wagon",
        "a little wagon full of berries in a shining row",
        "A wheel could sink there. Then the berries might tumble below.",
        "tumble",
        "get the wagon past the hole",
        "One wheel gave a shaky squeak, and the wagon rocked so low",
        tags={"wagon", "berries"}
    ),
    "seeds": Problem(
        "seeds",
        "carry seed packets to the patch",
        "seed packets",
        "three seed packets tied with string in a tidy little bow",
        "Loose dirt could make you slide, and the seeds might scatter where they blow.",
        "scatter",
        "clear the loose dirt",
        "The path went slick with loosened dirt, not safe for careful toes",
        tags={"seeds", "garden"}
    ),
}

HAZARDS = {
    "fresh_hole": Hazard(
        "fresh_hole",
        "it scratched and kicked",
        "and tossed dark crumbs in a round new ring",
        "a fresh hole opened",
        tags={"hole", "digging"}
    ),
    "soil_mound": Hazard(
        "soil_mound",
        "it burrowed in a hurry",
        "and pushed a lumpy mound up like a spring",
        "a soil mound rose",
        tags={"mound", "digging"}
    ),
}

TOOLS = {
    "board": Tool(
        "board",
        "board",
        "a flat wooden board by the shed",
        solves={"watering", "wagon"},
        method_line="They laid the board across the rough place like a bridge for careful feet",
        ending_line="Across that snug and steady board",
        tags={"board", "bridge"}
    ),
    "broom": Tool(
        "broom",
        "broom",
        "a straw broom leaning by the gate",
        solves={"seeds"},
        method_line="They swept the loose dirt off the path in soft and whispery strokes",
        ending_line="With the path brushed clean by the broom",
        tags={"broom", "sweep"}
    ),
    "basket": Tool(
        "basket",
        "basket",
        "a berry basket with a strong round handle",
        solves={"watering"},
        method_line="They set the can in the basket and carried it level with two hands",
        ending_line="With the can riding safe in the basket",
        tags={"basket", "carry"}
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Poppy", "June", "Ivy", "Tess", "Lucy", "Ada"]
BOY_NAMES = ["Finn", "Milo", "Owen", "Toby", "Ben", "Eli", "Sam", "Leo"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    hazard: str
    tool: str
    child_name: str
    child_type: str
    helper_type: str
    helper_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "gopher": [(
        "What is a gopher?",
        "A gopher is a small burrowing animal that digs tunnels and pushes soil up from the ground. Because it digs so quickly, it can make little holes or mounds in a yard or field."
    )],
    "wild": [(
        "What does wild mean for an animal?",
        "A wild animal lives outside on its own instead of living as a pet in a house. It follows its own habits, like digging, hiding, and finding food."
    )],
    "problem_solving": [(
        "What does problem solving mean?",
        "Problem solving means you stop, notice what is wrong, and think of a good way to fix it. A good solution matches the problem instead of being a random idea."
    )],
    "board": [(
        "How can a board help on rough ground?",
        "A flat board can make a steadier way across a small hole or bump. It helps spread weight so feet or wheels do not sink as easily."
    )],
    "broom": [(
        "What does a broom do?",
        "A broom sweeps dirt, dust, or leaves away from a place you want to keep clear. It is useful when the problem is loose stuff on the ground."
    )],
    "basket": [(
        "Why can a basket help carry something?",
        "A basket can hold an object steady so it does not tip as much while you walk. Handles also make it easier to carry with care."
    )],
    "seeds": [(
        "Why do people plant seeds?",
        "People plant seeds so new plants can grow. Seeds need the right place and care, so you do not want them to spill everywhere by accident."
    )],
    "berries": [(
        "Why should berries be carried gently?",
        "Berries are soft and can get squashed or spilled if a wagon tips. Carrying them gently helps keep them clean and whole."
    )],
    "water": [(
        "Why might water spill from a can?",
        "Water can slosh out when a can tips or wobbles. That is why careful walking and a steady path matter."
    )],
}
KNOWLEDGE_ORDER = ["gopher", "wild", "problem_solving", "board", "broom", "basket",
                   "seeds", "berries", "water"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p, t, s = f["problem"], f["tool"], f["setting"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "wild" and "gopher" and features problem solving in {s.place}.',
        f"Tell a gentle story where a child faces a {p.id} problem after a wild gopher digs in the ground, then uses {t.label} to fix it.",
        f'Write a child-facing rhyming tale in which the right tool solves the trouble, and the ending shows the child can finish the job safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    problem, tool, setting = f["problem"], f["tool"], f["setting"]
    out = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.label if child.label else 'a child'}, and {helper.id}, who were in {setting.place}. A wild gopher caused the trouble they had to solve."
        ),
        (
            "What problem did the wild gopher make?",
            f"The gopher dug up the ground and made {problem.effect}. That made it risky for {child.id} to {problem.task} because the {problem.item} might {problem.risk_word}."
        ),
        (
            f"How did {child.id} solve the problem?",
            f"{child.id} did not rush. {child.pronoun().capitalize()} looked carefully, chose {tool.phrase}, and used it because it could {problem.fix_need}."
        ),
        (
            "Why was that a good solution?",
            f"It was a good solution because it matched the exact trouble in the ground. After they used the {tool.label}, the risky spot became safe enough to finish the job."
        ),
    ]
    if f.get("solved"):
        out.append((
            "How did the story end?",
            f"It ended with {child.id} finishing the task safely and feeling proud. The last picture shows that the problem really changed, because the path was steadier and the important thing was no longer in danger."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gopher", "wild", "problem_solving"} | set(f["tool"].tags) | set(f["problem"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "watering", "fresh_hole", "board", "Nell", "girl", "mother", "Mom"),
    StoryParams("meadow", "wagon", "soil_mound", "board", "Finn", "boy", "father", "Dad"),
    StoryParams("orchard", "seeds", "fresh_hole", "broom", "Poppy", "girl", "mother", "Mom"),
    StoryParams("garden", "watering", "soil_mound", "basket", "Milo", "boy", "father", "Dad"),
]


ASP_RULES = r"""
valid(S, P, H, T) :- setting(S), problem(P), hazard(H), tool(T), solves(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for pid in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify smoke test.")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Wild gopher problem-solving rhyming story world."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool and not fits(PROBLEMS[args.problem], TOOLS[args.tool]):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, problem, hazard, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father"])
    helper_name = "Mom" if helper_type == "mother" else "Dad"
    return StoryParams(setting, problem, hazard, tool, child_name, gender, helper_type, helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        HAZARDS[params.hazard],
        TOOLS[params.tool],
        params.child_name,
        params.child_type,
        params.helper_name,
        params.helper_type,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, hazard, tool) combos:\n")
        for setting, problem, hazard, tool in combos:
            print(f"  {setting:8} {problem:9} {hazard:10} {tool}")
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
            header = f"### {p.child_name}: {p.problem} at {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
