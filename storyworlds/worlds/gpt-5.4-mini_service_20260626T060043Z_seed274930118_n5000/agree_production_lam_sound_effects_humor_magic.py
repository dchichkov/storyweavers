#!/usr/bin/env python3
"""
A superhero-style storyworld about a production set, an escaped troublemaker
who is on the lam, and a brave fix built from sound effects, humor, and magic.

The world is intentionally small and constraint-driven:
- a city studio is trying to finish a production
- a sneaky foe is on the lam after causing trouble
- the hero and a helper disagree at first, then agree on a magical, funny plan
- the plan uses sound effects, humor, and magic to calm the crowd and protect
  the production
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    helps: set[str]
    use_line: str
    finish_line: str


@dataclass
class Problem:
    id: str
    label: str
    action: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    hero_name: str
    hero_gender: str
    helper_role: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


TRAITS = ["brave", "quick", "cheerful", "clever", "bold", "gentle"]
GIRL_NAMES = ["Maya", "Tara", "Nina", "Zoe", "Lina", "Ivy"]
BOY_NAMES = ["Owen", "Leo", "Kai", "Milo", "Evan", "Jude"]

SETTINGS = {
    "studio": Setting(place="the city studio", afford={"production"}),
    "square": Setting(place="the bright town square", afford={"production"}),
    "rooftop": Setting(place="the rooftop set", afford={"production"}),
}

PROBLEMS = {
    "lam": Problem(
        id="lam",
        label="the runaway prankster",
        action="slip away on the lam",
        mess="chaos",
        risk="the cameras would miss the big scene",
        tags={"lam", "chaos"},
    ),
    "fog": Problem(
        id="fog",
        label="the fog machine glitch",
        action="smother the set in fog",
        mess="fog",
        risk="the actors could not see the marks",
        tags={"production", "fog"},
    ),
    "echo": Problem(
        id="echo",
        label="a noisy echo",
        action="bounce sound all over the set",
        mess="noise",
        risk="the lines would sound wrong",
        tags={"sound", "production"},
    ),
}

TOOLS = {
    "laugh": Tool(
        id="laugh",
        label="a joke spark",
        kind="humor",
        helps={"lam", "noise"},
        use_line="tell a silly joke at just the right moment",
        finish_line="the whole crew laughed, and the mood turned bright",
    ),
    "boom": Tool(
        id="boom",
        label="comic boom pops",
        kind="sound",
        helps={"lam", "noise"},
        use_line="tap the megaphone and let out a comic boom",
        finish_line="BOOM-POW! the sound bounced like a friendly drum",
    ),
    "glow": Tool(
        id="glow",
        label="a magic glow wand",
        kind="magic",
        helps={"lam", "fog"},
        use_line="wave the glow wand and whisper a tiny spell",
        finish_line="sparkles shimmered, and the troublemaker slowed down",
    ),
}

CURATED = [
    StoryParams("studio", "lam", "glow", "Maya", "girl", "captain", "brave"),
    StoryParams("square", "echo", "laugh", "Owen", "boy", "partner", "clever"),
    StoryParams("rooftop", "fog", "boom", "Nina", "girl", "sidekick", "bold"),
]


def valid_combo(place: str, problem: str, tool: str) -> bool:
    p = PROBLEMS[problem]
    t = TOOLS[tool]
    return place in SETTINGS and "production" in SETTINGS[place].afford and p.id in t.helps


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for prob in PROBLEMS:
            for tool in TOOLS:
                if valid_combo(place, prob, tool):
                    out.append((place, prob, tool))
    return out


def hero_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} superhero who watched every corner of the city.")


def setup(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} and {helper.label} worked on a big production at {world.setting.place}, "
        f"where everyone was trying to finish one bright scene."
    )
    world.say(
        f"But {problem.label} was on the lam, and {problem.risk}."
    )


def tension(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["doubt"] = helper.memes.get("doubt", 0) + 1
    world.say(
        f"{hero.id} wanted to rush after the problem at once, but {helper.id} shook {helper.pronoun('possessive')} head."
    )
    world.say(
        f"\"We need a better plan,\" {helper.pronoun()} said, because {problem.risk}."
    )


def choose_tool(world: World, tool: Tool) -> None:
    world.say(
        f"Then they agreed to use {tool.label}: {tool.use_line}."
    )


def resolve(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"{tool.finish_line}. The runaway trouble melted from the stage, and the production stayed safe."
    )
    world.say(
        f"{hero.id} and {helper.id} grinned like true teammates, ready for the next mission."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        traits=[params.trait, "superhero"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="adult",
        label=f"the {params.helper_role}",
        traits=["helpful"],
    ))
    villain = world.add(Entity(
        id="Trouble",
        kind="character",
        type="adult",
        label=problem.label,
        traits=["sneaky", "on the lam"],
    ))
    prop = world.add(Entity(
        id="Production",
        kind="thing",
        type="production",
        label="the production",
        owner=helper.id,
    ))

    world.facts.update(hero=hero, helper=helper, villain=villain, prop=prop, problem=problem, tool=tool)

    hero_intro(world, hero)
    world.para()
    setup(world, hero, helper, problem)
    world.para()
    tension(world, hero, helper, problem)
    choose_tool(world, tool)
    world.para()
    resolve(world, hero, helper, problem, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        f'Write a short superhero story with the word "agree" where {hero.id} and a helper agree on a plan.',
        f"Tell a child-friendly superhero story about a production problem on the lam that is solved with {tool.kind}, humor, and magic.",
        f'Write a bright story for young kids that includes the words "production" and "lam" and ends with a happy rescue of the set.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, a {hero.traits[0]} hero who helped protect the production.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry about the plan?",
            answer=f"{helper.label.capitalize()} worried because {problem.risk}, so rushing in would not help the production.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.id} agree to use?",
            answer=f"They agreed to use {tool.label}, which fit the problem and helped save the scene.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The troublemaker was stopped, the production stayed safe, and {hero.id} and {helper.id} ended smiling together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story is a tale about a brave hero who helps others and solves a big problem.",
        ),
        QAItem(
            question="What is sound effects?",
            answer="Sound effects are special noises made to help a story, show action, or make a scene feel exciting.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the part of a story that makes people smile or laugh.",
        ),
        QAItem(
            question="What is magic?",
            answer="Magic is a special kind of power that can make surprising things happen in a story.",
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
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(P, Pr, T) :- place(P), problem(Pr), tool(T), afford(P, production), helps(T, Pr).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in SETTINGS[pid].afford:
            lines.append(asp.fact("afford", pid, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        for h in TOOLS[tid].helps:
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with sound effects, humor, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-role", choices=["captain", "partner", "sidekick"])
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
    combos = valid_combos()
    if args.place or args.problem or args.tool:
        combos = [c for c in combos
                  if (args.place is None or c[0] == args.place)
                  and (args.problem is None or c[1] == args.problem)
                  and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_role = args.helper_role or rng.choice(["captain", "partner", "sidekick"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, problem, tool, name, gender, helper_role, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
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
            header = f"### {p.hero_name}: {p.problem} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
