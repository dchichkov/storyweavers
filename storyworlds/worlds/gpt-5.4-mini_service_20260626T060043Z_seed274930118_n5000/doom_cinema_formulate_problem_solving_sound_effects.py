#!/usr/bin/env python3
"""
storyworlds/worlds/doom_cinema_formulate_problem_solving_sound_effects.py
========================================================================

A small folk-tale storyworld about a village cinema, a worried warning of doom,
and a kind plan that is formulated in time. The world is intentionally narrow:
one small problem, one sensible way to solve it, and sound effects that help
the tale feel alive.

The seed words are woven into the premise:
- doom
- cinema
- formulate

The style aim is folk tale: simple, concrete, and lightly rhythmic.
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
# Core world model
# ---------------------------------------------------------------------------
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    danger: str
    sound: str
    fix: str
    keyword: str = "doom"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.problem_active: bool = False

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.problem_active = self.problem_active
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cinema": Setting(place="the little cinema", indoor=True, affords={"film"}),
    "hall": Setting(place="the village hall", indoor=True, affords={"film"}),
    "barn": Setting(place="the old barn", indoor=True, affords={"film"}),
}

PROBLEMS = {
    "doom": Problem(
        id="doom",
        verb="watch the doom scene",
        gerund="watching the doom scene",
        danger="the lantern will go out",
        sound="whirr-clank",
        fix="steady the projector",
        keyword="doom",
        tags={"doom", "sound"},
    ),
    "rattle": Problem(
        id="rattle",
        verb="hear the rattling wheel",
        gerund="listening to the rattling wheel",
        danger="the film will skip and blur",
        sound="rat-a-tat",
        fix="steady the wheel",
        keyword="cinema",
        tags={"cinema", "sound"},
    ),
    "whistle": Problem(
        id="whistle",
        verb="follow the whistle in the dark",
        gerund="following the whistle in the dark",
        danger="the night watch will scatter",
        sound="fwee-oo",
        fix="cover the lamp",
        keyword="formulate",
        tags={"formulate", "sound"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a bright lantern",
        guards={"dark", "fade"},
        prep="place the lantern beside the machine",
        tail="placed the lantern beside the machine",
    ),
    "cloth": Tool(
        id="cloth",
        label="cloth",
        phrase="a soft cloth",
        guards={"rattle", "skip"},
        prep="wrap the wheel with a soft cloth",
        tail="wrapped the wheel with a soft cloth",
    ),
    "hood": Tool(
        id="hood",
        label="hood",
        phrase="a paper hood",
        guards={"whistle", "scatter"},
        prep="make a paper hood for the lamp",
        tail="made a paper hood for the lamp",
    ),
}

HERO_NAMES = ["Milo", "Tara", "Anya", "Bram", "Nia", "Pip", "Lena", "Oren"]
HELPER_NAMES = ["Grandmother", "Grandfather", "Aunt", "Uncle", "Keeper"]
TRAITS = ["curious", "gentle", "brave", "patient", "wise"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def problem_is_at_risk(problem: Problem, place: Setting) -> bool:
    return "film" in place.affords


def choose_tool(problem: Problem) -> Optional[Tool]:
    if problem.id == "doom":
        return TOOLS["lantern"]
    if problem.id == "rattle":
        return TOOLS["cloth"]
    if problem.id == "whistle":
        return TOOLS["hood"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            tool = choose_tool(prob)
            if tool and problem_is_at_risk(prob, setting):
                combos.append((place_id, prob_id, tool.id))
    return combos


def explain_rejection(problem: Problem) -> str:
    return f"(No story: the chosen problem does not have a fitting folk-tale fix.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_at_risk(P, S) :- problem(P), setting(S), affords(S, film).
fixable(P, T) :- problem(P), tool(T), guards(T, G), needs(P, G).
valid_story(S, P, T) :- problem_at_risk(P, S), fixable(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("needs", pid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a cinema, doom, and a plan.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    if args.problem and args.tool:
        if choose_tool(PROBLEMS[args.problem]).id != args.tool:
            raise StoryError(explain_rejection(PROBLEMS[args.problem]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, helper=helper, trait=trait)


def problem_line(problem: Problem) -> str:
    return {
        "doom": "The machine gave a low doom-whirr in the dark.",
        "rattle": "The wheel made a rat-a-tat sound and shook the frame.",
        "whistle": "The lamp let out a thin fwee-oo and made the cats blink.",
    }[problem.id]


def tell(setting: Setting, problem: Problem, tool: Tool, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="elder", label=helper_name))
    machine = world.add(Entity(id="machine", type="projector", label="projector", caretaker=helper.id))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    tool_ent.worn_by = hero.id

    hero.memes["curiosity"] = 1
    world.say(f"{hero_name} was a {trait} child who loved the lantern glow of {setting.place}.")
    world.say(f"Each evening, {hero_name} liked the old screen and the stories it carried.")
    world.say(f"One night, {problem_line(problem)}")
    world.say(f"That sound felt like a little doom to the room, and the folk in the seats grew quiet.")

    world.para()
    world.say(f"{hero_name} listened, then spoke softly: \"We should formulate a plan.\"")
    hero.memes["resolve"] = 1
    helper.memes["worry"] = 1
    world.say(f"{helper_name} nodded, because the room needed a calm hand and a clear thought.")
    world.say(f"They looked at the {problem.fix} and chose the right tool: {tool.phrase}.")

    world.para()
    if problem.id == "doom":
        world.say(f"{helper_name} said, \"Hold the light steady.\"")
        world.say(f"{hero_name} helped {tool.prep}, and the projector answered with a soft hum.")
    elif problem.id == "rattle":
        world.say(f"{helper_name} said, \"Quiet the wheel.\"")
        world.say(f"{hero_name} helped {tool.prep}, and the frame went still again.")
    else:
        world.say(f"{helper_name} said, \"Keep the lamp from wandering.\"")
        world.say(f"{hero_name} helped {tool.prep}, and the whistle faded away.")
    world.say(f"After that, the film sailed on with a gentle flicker, and the children breathed again.")
    world.say(f"By the last scene, the cinema was safe, and the night sounded like peace.")

    world.facts.update(
        hero=hero,
        helper=helper,
        machine=machine,
        tool=tool_ent,
        setting=setting,
        problem=problem,
        tool_def=tool,
        problem_fix=problem.fix,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for children about a {f["setting"].place} where a hint of doom appears, but a wise plan is formulated.',
        f"Tell a gentle story about {f['hero'].id} and {f['helper'].id} solving a problem at the cinema with a sound like {f['problem'].sound}.",
        f"Make a simple tale using the words doom, cinema, and formulate, and end with a happy fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    tool = f["tool_def"]
    return [
        QAItem(
            question=f"Who helped {hero.id} with the problem at {f['setting'].place}?",
            answer=f"{helper.id} helped {hero.id} think clearly and solve the problem together.",
        ),
        QAItem(
            question=f"What sound warned the room that something was wrong?",
            answer=f"It was a {problem.sound} sound, and it made the room feel a little spooky.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} do before the film could continue?",
            answer=f"They formulated a plan and used {tool.phrase} to fix the problem.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The problem was solved, the cinema stayed safe, and the film went on in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cinema?",
            answer="A cinema is a place where people sit and watch moving pictures on a screen.",
        ),
        QAItem(
            question="What does it mean to formulate a plan?",
            answer="To formulate a plan means to make a careful plan by thinking about what to do next.",
        ),
        QAItem(
            question="Why do sound effects matter in stories?",
            answer="Sound effects help a story feel lively by letting readers imagine the noises in the scene.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cinema", problem="doom", tool="lantern", name="Milo", helper="Grandmother", trait="curious"),
    StoryParams(place="hall", problem="rattle", tool="cloth", name="Tara", helper="Aunt", trait="gentle"),
    StoryParams(place="barn", problem="whistle", tool="hood", name="Bram", helper="Uncle", trait="brave"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], TOOLS[params.tool],
                 params.name, params.helper, params.trait)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (place, problem, tool) combos:\n")
        for place, problem, tool in triples:
            print(f"  {place:8} {problem:8} {tool:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
