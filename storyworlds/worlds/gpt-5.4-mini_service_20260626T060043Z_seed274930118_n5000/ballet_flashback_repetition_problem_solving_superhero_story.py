#!/usr/bin/env python3
"""
A small superhero-flavored ballet story world with flashback, repetition, and
problem solving.

The hero is a young ballet-powered helper who faces a practical problem on the
way to a performance. The story engine simulates the pressure, the remembered
lesson, the repeated attempts, and the final fix so the prose can end with a
clear changed state.
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

TITLE = "ballet_flashback_repetition_problem_solving_superhero_story"

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    danger: str
    solve_with: str
    resolution: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "studio": Setting(place="the dance studio", affords={"stuck_music_box", "jammed_curtain"}),
    "theater": Setting(place="the old theater", affords={"stuck_music_box", "jammed_curtain"}),
    "rooftop": Setting(place="the rooftop stage", affords={"windy_music_box", "jammed_curtain"}),
}

PROBLEMS = {
    "stuck_music_box": Problem(
        id="stuck_music_box",
        label="music box",
        phrase="the small music box that played the ballet tune",
        danger="the song would not start",
        solve_with="tiny_key",
        resolution="the spring clicked free and the song began",
        clue="a little key slot under the brass lid",
        tags={"music", "ballet", "flashback"},
    ),
    "jammed_curtain": Problem(
        id="jammed_curtain",
        label="curtain",
        phrase="the heavy curtain across the stage",
        danger="the dancers could not come out",
        solve_with="tug_rope",
        resolution="the rope slid loose and the curtain rose",
        clue="a knot caught on the rail",
        tags={"stage", "repetition", "problem_solving"},
    ),
    "windy_music_box": Problem(
        id="windy_music_box",
        label="music box",
        phrase="the wind-tossed music box on the rooftop stage",
        danger="the tune kept skipping away",
        solve_with="weighted_clip",
        resolution="the clip held the lid steady and the melody stayed put",
        clue="the lid kept flipping in the breeze",
        tags={"wind", "ballet", "problem_solving"},
    ),
}

TOOLS = {
    "tiny_key": Tool(
        id="tiny_key",
        label="a tiny silver key",
        phrase="a tiny silver key on a chain",
        helps={"stuck_music_box"},
        tags={"music"},
    ),
    "tug_rope": Tool(
        id="tug_rope",
        label="a bright tug rope",
        phrase="a bright tug rope with a star knot",
        helps={"jammed_curtain"},
        tags={"stage"},
    ),
    "weighted_clip": Tool(
        id="weighted_clip",
        label="a weighted clip",
        phrase="a weighted clip shaped like a star",
        helps={"windy_music_box"},
        tags={"wind"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Tia", "Nora", "Zuri", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Milo", "Jace"]
TRAITS = ["brave", "gentle", "quick", "cheerful", "spirited"]


class World:
    def __init__(self, setting: Setting):
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, setting in SETTINGS.items():
        for prob in setting.affords:
            for tool_id, tool in TOOLS.items():
                if prob in tool.helps:
                    combos.append((p, prob, tool_id))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.solve_with))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for prob in sorted(t.helps):
            lines.append(asp.fact("helps", tid, prob))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Problem, Tool) :- affords(Place, Problem), helps(Tool, Problem).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero ballet story world with flashback and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mentor", choices=["teacher", "aunt", "coach"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    prob = PROBLEMS[problem]
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name is None:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    else:
        name = args.name
    mentor = args.mentor or rng.choice(["teacher", "aunt", "coach"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, gender=gender, mentor=mentor, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    mentor = world.add(Entity(id="Mentor", kind="character", type=params.mentor))
    problem = world.add(Entity(id="Problem", type=PROBLEMS[params.problem].label, phrase=PROBLEMS[params.problem].phrase))
    tool = world.add(Entity(id="Tool", type=TOOLS[params.tool].label, phrase=TOOLS[params.tool].phrase))
    world.facts.update(hero=hero, mentor=mentor, problem=problem, tool=tool, params=params)
    return world


def generate_story(world: World) -> None:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    prob = PROBLEMS[p.problem]
    tool = TOOLS[p.tool]

    hero.memes["joy"] = 1
    hero.memes["hope"] = 1
    world.say(f"{hero.id} was a {p.trait} little superhero who loved ballet more than anything.")
    world.say(f"{hero.pronoun().capitalize()} practiced a bright twirl, and {world.setting.place} felt ready for a show.")
    world.say(f"{hero.id} wore {prob.phrase} because tonight the dance mattered like a rescue.")

    world.para()
    hero.memes["worry"] = 1
    world.say(f"But then {prob.phrase} became stuck, and {prob.danger}.")
    world.say(f"{hero.id} remembered a flashback: {p.mentor} had once said, \"When a thing is stuck, look for the small clue first.\"")
    world.say(f"The clue was {prob.clue}, so {hero.id} took a slow breath and tried to solve it.")

    world.para()
    hero.memes["focus"] = 1
    if p.problem == "jammed_curtain":
        world.say(f"{hero.id} pulled the rope once. Nothing moved.")
        world.say(f"{hero.id} pulled the rope again. The knot still held.")
        world.say(f"{hero.id} pulled the rope a third time, and the knot slipped free.")
    elif p.problem == "stuck_music_box":
        world.say(f"{hero.id} turned the tiny key once. The box stayed quiet.")
        world.say(f"{hero.id} turned the tiny key again. The spring only gave a little click.")
        world.say(f"{hero.id} turned the tiny key one more time, and the lid finally opened.")
    else:
        world.say(f"{hero.id} clipped the lid once. The wind bumped it away.")
        world.say(f"{hero.id} clipped it again. The tune still wobbled.")
        world.say(f"{hero.id} clipped it a third time, and the lid stayed steady.")

    world.para()
    hero.memes["pride"] = 1
    hero.memes["worry"] = 0
    hero.memes["confidence"] = 1
    world.say(f"At last, {prob.resolution}.")
    world.say(f"{hero.id} smiled, and the ballet could begin at last.")
    world.say(f"{hero.id} leaped, spun, and landed softly while {world.setting.place} shone like a stage made for heroes.")

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    prob = PROBLEMS[p.problem]
    return [
        f"Write a short superhero story for a child named {p.name} who loves ballet and solves a problem by trying again.",
        f"Tell a gentle story with a flashback, repeated attempts, and a clever fix at {world.setting.place}.",
        f"Write a ballet adventure where {p.name} remembers a lesson from {p.mentor} and saves the performance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    prob = PROBLEMS[p.problem]
    tool = TOOLS[p.tool]
    hero: Entity = world.facts["hero"]
    return [
        QAItem(
            question=f"What did {hero.id} love more than anything?",
            answer=f"{hero.id} loved ballet more than anything.",
        ),
        QAItem(
            question=f"What problem made the dance hard at {world.setting.place}?",
            answer=f"The {prob.label} was stuck, so {prob.danger}.",
        ),
        QAItem(
            question=f"What lesson came back in the flashback?",
            answer=f"{p.mentor} had said to look for the small clue first when something is stuck.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} solved it by using {tool.phrase} and trying again and again until {prob.resolution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is ballet?", answer="Ballet is a kind of dance with careful steps, turns, and jumps."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is when the story briefly remembers something that happened before."),
        QAItem(question="Why do people try again when something does not work?", answer="Trying again can help you solve a problem when the first try fails."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="studio", problem="stuck_music_box", tool="tiny_key", name="Mira", gender="girl", mentor="teacher", trait="brave"),
    StoryParams(place="theater", problem="jammed_curtain", tool="tug_rope", name="Eli", gender="boy", mentor="coach", trait="spirited"),
    StoryParams(place="rooftop", problem="windy_music_box", tool="weighted_clip", name="Nora", gender="girl", mentor="aunt", trait="cheerful"),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: {tool.label} does not help with {problem.label} in this world.)"


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
