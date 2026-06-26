#!/usr/bin/env python3
"""
A standalone Storyweavers world: chemistry, a plough, suspense, inner monologue,
and problem solving, told with a light comic tone.

Seed idea:
A curious child is helping at a small farm science day. They want to show a tiny
chemistry trick, but the plough is stuck, the helpers are waiting, and the child
has to think fast. The story turns on a silly but sensible fix that uses basic
chemistry and a little teamwork.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stuck": 0.0, "messy": 0.0, "bored": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "pride": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the farm yard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Experiment:
    id: str
    label: str
    keyword: str
    ingredients: list[str]
    effect: str
    clue: str
    soothed_by: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_lines: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "farm": Setting(place="the farm yard", affords={"chemistry", "plough"}),
    "shed": Setting(place="the old tool shed", affords={"chemistry", "plough"}),
    "yard": Setting(place="the back yard", affords={"chemistry", "plough"}),
}

EXPERIMENTS = {
    "bubbles": Experiment(
        id="bubbles",
        label="bubble fizz",
        keyword="chemistry",
        ingredients=["baking soda", "vinegar"],
        effect="made a foamy fizz that rose like a tiny volcano",
        clue="the fizz could loosen crusty mud",
        soothed_by="the foamy bubbles"
    ),
    "sparkle": Experiment(
        id="sparkle",
        label="sparkle test",
        keyword="chemistry",
        ingredients=["salt", "water"],
        effect="made a glittery swirl in the jar",
        clue="the swirl showed the mixture had changed",
        soothed_by="the careful mixing"
    ),
}

TOOLS = {
    "plough": Tool(
        id="plough",
        label="plough",
        phrase="the heavy old plough",
        use="pull the plough free",
        helps="the loosened mud slipped away from the metal"
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a long rope",
        use="tug the plough",
        helps="the rope gave everyone something to hold"
    ),
}


@dataclass
class StoryParams:
    place: str
    experiment: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for exp in EXPERIMENTS:
            for tool in TOOLS:
                if {"chemistry", "plough"}.issubset(setting.affords):
                    combos.append((place, exp, tool))
    return combos


def explain_rejection(place: str, exp: str, tool: str) -> str:
    return (
        f"(No story: the chosen combination {place}/{exp}/{tool} does not fit "
        f"the tiny world rules. Pick one of the supported settings and tools.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, exp: Experiment, tool: Tool) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} was a {child.type} who loved little experiments and big, silly problems."
    )
    world.say(
        f"{child.id} had brought {exp.label} ingredients and kept glancing at {tool.phrase}."
    )
    world.say(
        f"{child.id} kept thinking, {repr('If the plough moves, everyone will cheer. If it does not, I will have to be clever.')} "
        f"That thought made {child.pronoun('object')} wiggle with nervous excitement."
    )
    world.say(
        f"Beside {child.pronoun('object')}, {helper.id} waited with a patient face and a very dusty hat."
    )


def set_up(world: World, child: Entity, exp: Experiment, tool: Tool) -> None:
    world.say(
        f"In {world.setting.place}, {child.id} mixed {exp.ingredients[0]} and {exp.ingredients[1]}."
    )
    world.say(
        f"The mixture {exp.effect}, which was impressive in the way only a tiny mess can be."
    )
    child.memes["joy"] += 1
    world.facts["experiment_effect"] = exp.effect
    world.facts["experiment_clue"] = exp.clue


def suspense(world: World, child: Entity, tool: Tool) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} looked at {tool.phrase} and saw that it had sunk deep into the mud."
    )
    world.say(
        f"No one spoke for a moment, which made the whole yard feel extra serious for about three seconds."
    )
    world.say(
        f"{child.id} thought, {repr('Please move. Please move. If you are secretly a stubborn metal turtle, move anyway.')} "
        f"and tried not to laugh at {child.pronoun('object')} own panic."
    )


def problem_solve(world: World, child: Entity, helper: Entity, exp: Experiment, tool: Tool) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} noticed that {exp.clue}, and {child.id} had an idea."
    )
    world.say(
        f"{child.id} said, {repr('If the mud is holding on, maybe we can make it less sticky first.')} "
        f"That sounded much smarter than simply staring at the plough."
    )
    world.say(
        f"So {child.id} poured a little of the experiment onto the muddy spot."
    )
    world.say(
        f"The {exp.soothed_by} softened the mud, and {helper.id} gave a surprised nod."
    )
    tool_state = world.get(tool.id)
    tool_state.meters["stuck"] = max(0.0, tool_state.meters["stuck"] - 1.0)
    world.facts["fixed_by_experiment"] = True


def finish(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    tool_state = world.get(tool.id)
    if tool_state.meters["stuck"] > 0:
        raise StoryError("The plough never became free, so there is no honest ending.")
    world.say(
        f"After one careful tug, the plough slid free with a squeak that sounded almost like a joke."
    )
    world.say(
        f"{helper.id} laughed, {child.id} laughed, and even the mud seemed embarrassed."
    )
    world.say(
        f"By the end, {child.id} had solved the problem, saved the day, and got exactly one splat of mud on {child.pronoun('possessive')} shoe."
    )
    child.memes["joy"] += 2
    child.memes["pride"] += 2
    world.facts["resolved"] = True


def tell(setting: Setting, exp: Experiment, tool: Tool, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    plough = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase))
    plough.meters["stuck"] = 1.0
    world.facts.update(
        child=child,
        helper=helper,
        plough=plough,
        experiment=exp,
        tool=tool,
        trait=trait,
        place=setting.place,
    )

    introduce(world, child, helper, exp, tool)
    world.para()
    set_up(world, child, exp, tool)
    suspense(world, child, tool)
    world.para()
    problem_solve(world, child, helper, exp, tool)
    finish(world, child, helper, tool)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny suspense story for a child who uses {f["experiment"].keyword} to help a {f["tool"].label}.',
        f"Tell a small comedy about {f['child'].id} thinking hard when the {f['tool'].label} is stuck in mud.",
        f"Write a child-friendly story where {f['child'].id} uses a chemistry trick to solve a plough problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    exp = f["experiment"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What problem did {child.id} have in {world.setting.place}?",
            answer=f"{child.id} had to free the {tool.label}, which was stuck in the mud."
        ),
        QAItem(
            question=f"What did {child.id} use to help the {tool.label} move?",
            answer=f"{child.id} used {exp.ingredients[0]} and {exp.ingredients[1]} to make a fizz that loosened the mud."
        ),
        QAItem(
            question=f"How did the story change from suspense to relief?",
            answer=(
                f"At first everyone worried because the {tool.label} would not move. "
                f"Then {child.id} used {exp.soothed_by}, the mud loosened, and {helper.id} could help pull it free."
            ),
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt proud and happy after solving the problem and making the {tool.label} move."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chemistry?",
            answer="Chemistry is the study of what stuff is made of and how different materials change when they mix."
        ),
        QAItem(
            question="What is a plough?",
            answer="A plough is a heavy tool that helps turn soil so plants can grow in it."
        ),
        QAItem(
            question="Why can vinegar and baking soda make bubbles?",
            answer="They react with each other and make a gas, and that gas creates lots of bubbles and foam."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(P) :- setting(P), affords(P, chemistry), affords(P, plough).
valid_story(P, E, T) :- setting_ok(P), experiment(E), tool(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid in EXPERIMENTS:
        lines.append(asp.fact("experiment", eid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Chemistry and plough comedy storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--experiment", choices=EXPERIMENTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["curious", "brave", "silly", "careful", "earnest"])
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.experiment is None or c[1] == args.experiment)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, exp, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = ["Mia", "Leo", "Nina", "Owen", "Ivy", "Sam", "Zoe", "Max"]
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(["curious", "brave", "silly", "careful", "earnest"])
    return StoryParams(place=place, experiment=exp, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EXPERIMENTS[params.experiment], TOOLS[params.tool],
                 params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show valid_story/3."))
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
        curated = [
            StoryParams("farm", "bubbles", "plough", "Mia", "girl", "father", "curious"),
            StoryParams("shed", "sparkle", "rope", "Leo", "boy", "mother", "careful"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
