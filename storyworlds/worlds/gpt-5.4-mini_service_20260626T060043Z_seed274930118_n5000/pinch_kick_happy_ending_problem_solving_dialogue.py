#!/usr/bin/env python3
"""
storyworlds/worlds/pinch_kick_happy_ending_problem_solving_dialogue.py
======================================================================

A small adventure storyworld about a child who wants to explore, gets into a
pinch-and-kick problem, talks it through, and finds a happy ending.

Premise:
- A brave child goes on a small adventure in a garden or path.
- Something gets in the way: a prickly bundle, a stuck gate, a tangled rope,
  or a muddy patch.

Tension:
- The child tries to pinch or kick at the problem.
- That makes the situation worse or more uncomfortable.

Turn:
- A helpful companion suggests a safer, smarter move.

Resolution:
- They solve the problem together with dialogue, and the child ends the story
  happy, relieved, and ready for the next part of the adventure.

This is a standalone storyworld script for the Storyweavers repo.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
    adventure_flavor: str = ""


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    type: str
    danger: str
    trigger: str
    worsens_with: set[str]
    fix_action: str
    solve_action: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    advice: str
    action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "garden_path": Setting(
        place="the garden path",
        affordances={"pinch", "kick", "explore"},
        adventure_flavor="The garden path wound past beans, stones, and a little wooden gate.",
    ),
    "orchard_edge": Setting(
        place="the orchard edge",
        affordances={"pinch", "kick", "explore"},
        adventure_flavor="The orchard edge was full of apple leaves, low branches, and soft grass.",
    ),
    "river_trail": Setting(
        place="the river trail",
        affordances={"pinch", "kick", "explore"},
        adventure_flavor="The river trail had reeds, pebbles, and a narrow bridge to cross.",
    ),
}

PROBLEMS = {
    "thorn_bundle": Problem(
        id="thorn_bundle",
        label="thorn bundle",
        phrase="a prickly thorn bundle",
        type="thing",
        danger="it could poke small hands",
        trigger="pinch",
        worsens_with={"pinch", "kick"},
        fix_action="use a stick to lift it",
        solve_action="move it aside",
        location="by the path",
        tags={"prickly", "pinch"},
    ),
    "stuck_gate": Problem(
        id="stuck_gate",
        label="stuck gate",
        phrase="a stubborn little gate",
        type="thing",
        danger="it would not open when pushed or kicked",
        trigger="kick",
        worsens_with={"kick", "pinch"},
        fix_action="pull the latch gently",
        solve_action="open it carefully",
        location="at the edge of the path",
        tags={"gate", "kick"},
    ),
    "tangled_rope": Problem(
        id="tangled_rope",
        label="tangled rope",
        phrase="a rope tied in a messy knot",
        type="thing",
        danger="it would trap the cart wheel",
        trigger="pinch",
        worsens_with={"pinch", "kick"},
        fix_action="work the knot loose with fingers",
        solve_action="untie it",
        location="next to the cart",
        tags={"rope", "problem_solving"},
    ),
    "mud_patch": Problem(
        id="mud_patch",
        label="mud patch",
        phrase="a slippery mud patch",
        type="thing",
        danger="it could send someone sliding",
        trigger="kick",
        worsens_with={"kick"},
        fix_action="walk around it with care",
        solve_action="find the safe stepping stones",
        location="across the path",
        tags={"mud", "adventure"},
    ),
}

HELPERS = {
    "fox": Helper(
        id="fox",
        label="a little fox",
        type="fox",
        advice="Try a calmer way first",
        action="showed a safer path",
        tags={"adventure", "dialogue"},
    ),
    "bird": Helper(
        id="bird",
        label="a bright bird",
        type="bird",
        advice="Look closely and use your hands, not your feet",
        action="pointed with its wing",
        tags={"dialogue"},
    ),
    "grandpa": Helper(
        id="grandpa",
        label="grandpa",
        type="father",
        advice="Let's solve it together",
        action="helped with steady hands",
        tags={"problem_solving", "dialogue"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Sana", "Tia"]
BOY_NAMES = ["Eli", "Milo", "Jonah", "Toby", "Noah", "Finn"]


@dataclass
class StoryParams:
    place: str
    problem: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


def _hero_pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def reasonableness_gate(setting: Setting, problem: Problem) -> bool:
    return {"pinch", "kick"}.intersection(problem.worsens_with) and "explore" in setting.affordances


def select_problem(setting: Setting, rng: random.Random) -> Problem:
    choices = [p for p in PROBLEMS.values() if reasonableness_gate(setting, p)]
    if not choices:
        raise StoryError("No reasonable problem can be placed in this setting.")
    return rng.choice(sorted(choices, key=lambda p: p.id))


def select_helper(rng: random.Random) -> Helper:
    return rng.choice(sorted(HELPERS.values(), key=lambda h: h.id))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: pinch, kick, dialogue, problem solving, happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob in PROBLEMS.values():
            if reasonableness_gate(setting, prob):
                for helper in HELPERS.values():
                    combos.append((place, prob.id, helper.id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.problem:
        if not reasonableness_gate(SETTINGS[args.place], PROBLEMS[args.problem]):
            raise StoryError("That problem does not fit the chosen setting.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, problem, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, problem=problem, helper=helper, name=name, gender=gender)


def tell(setting: Setting, problem: Problem, helper: Helper, name: str, gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    pal = world.add(Entity(id=helper.id, kind="character", type=helper.type, label=helper.label))
    obstacle = world.add(Entity(id=problem.id, kind="thing", type=problem.type, label=problem.label, phrase=problem.phrase))
    world.facts.update(hero=hero, helper=pal, problem=obstacle, problem_cfg=problem, helper_cfg=helper)

    world.say(f"{hero.id} was a brave little {gender} who loved adventure.")
    world.say(f"One morning, {hero.id} set out along {setting.place} because {setting.adventure_flavor.lower()}")
    world.say(f"Near {problem.location}, {hero.id} found {problem.phrase}.")
    world.para()

    world.say(f'{hero.id} whispered, "I can handle this."')
    world.say(f"{hero.id} tried to {problem.trigger} the problem, but that only made {problem.danger}.")
    if problem.trigger == "pinch":
        world.say(f"{hero.id} pinched at it, then yelped when the prickles pressed back.")
    else:
        world.say(f"{hero.id} kicked at it, but the stubborn thing did not budge.")
    world.para()

    world.say(f"{pal.id} came close and said, \"{helper.advice}.\"")
    world.say(f'{hero.id} asked, "Then what should I do?"')
    world.say(f'{pal.id} answered, "{helper.action.capitalize()} and {problem.solve_action}."')
    world.say(f"{hero.id} nodded and worked with {pal.id}. Together they {problem.solve_action}.")
    world.say(f"In the end, {hero.id} smiled, the path was clear, and the adventure could go on.")
    world.say(f'{hero.id} laughed, "That was a good save!"')
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, problem = f["hero"], f["problem_cfg"]
    return [
        f"Write a short adventure story about {hero.id} encountering {problem.phrase} on a path.",
        f"Tell a child-friendly story with dialogue where a hero first tries to {problem.trigger} and then solves the problem wisely.",
        f"Write a happy-ending adventure featuring problem solving and a safe choice instead of more {problem.trigger}ing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem = f["hero"], f["helper"], f["problem_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} find on the path?",
            answer=f"{hero.id} found {problem.phrase} while exploring {world.setting.place}."
        ),
        QAItem(
            question=f"What did {hero.id} try first when faced with the problem?",
            answer=f"{hero.id} first tried to {problem.trigger} it, but that made things worse."
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.label} helped {hero.id} talk through the problem and solve it safely."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} smiling because the problem was fixed and the path was clear."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a trouble and choosing a smart way to fix it."
        ),
        QAItem(
            question="Why is dialogue useful?",
            answer="Dialogue is useful because people can share ideas, ask for help, and understand each other better."
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the trouble is resolved and the character feels safe, glad, or relieved."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], HELPERS[params.helper], params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} kind={e.kind} label={e.label}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    parts = ["== Story questions =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


ASP_RULES = r"""
valid(Place, Problem, Helper) :- setting(Place), problem(Problem), helper(Helper),
    place_affords(Place, explore), problem_worsens_with(Problem, pinch),
    problem_worsens_with(Problem, kick).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("place_affords", place, a))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for w in sorted(problem.worsens_with):
            lines.append(asp.fact("problem_worsens_with", pid, w))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("Only in python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="garden_path", problem="thorn_bundle", helper="fox", name="Mina", gender="girl"),
    StoryParams(place="orchard_edge", problem="stuck_gate", helper="grandpa", name="Eli", gender="boy"),
    StoryParams(place="river_trail", problem="tangled_rope", helper="bird", name="Nora", gender="girl"),
    StoryParams(place="garden_path", problem="mud_patch", helper="fox", name="Finn", gender="boy"),
]


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
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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


if __name__ == "__main__":
    main()
