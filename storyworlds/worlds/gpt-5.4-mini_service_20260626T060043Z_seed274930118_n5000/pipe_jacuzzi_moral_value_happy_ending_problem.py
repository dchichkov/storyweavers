#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pipe_jacuzzi_moral_value_happy_ending_problem.py
========================================================================================================

A small comedy storyworld about a leaky pipe, a grumpy jacuzzi, and a child
who solves the problem with a moral choice and a happy ending.

Premise:
- A home has a pipe, a jacuzzi, and a family member who wants comfort.
- A leak or clog makes the jacuzzi unusable or messy.
- A helpful character notices the problem, chooses an honest fix, and the
  house ends up peaceful again.

This world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes,
- a forward-simulated world model,
- a reasonableness gate for story generation,
- an inline ASP twin for parity verification.

The prose aims for:
- comedy,
- clear causal turns,
- a concrete repair,
- an ending image proving what changed.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    cause: str
    effect: str
    location: str
    risk: str
    fix: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    use_verb: str
    funny_finish: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bathroom": Setting(place="the bathroom", indoor=True, affords={"pipe", "jacuzzi"}),
    "spa": Setting(place="the tiny spa room", indoor=True, affords={"pipe", "jacuzzi"}),
    "basement": Setting(place="the basement", indoor=True, affords={"pipe"}),
}

PROBLEMS = {
    "leak": Problem(
        id="leak",
        cause="a loose pipe joint",
        effect="water dripped everywhere",
        location="pipe",
        risk="the floor got wet",
        fix="tighten the pipe",
        clue="the pipe whispered a silly drip-drip sound",
        tags={"pipe", "water", "comedy"},
    ),
    "clog": Problem(
        id="clog",
        cause="soap bubbles and a toy frog",
        effect="the jacuzzi would not bubble",
        location="jacuzzi",
        risk="the water stayed grumpy and still",
        fix="clear the drain",
        clue="the jacuzzi made a glum glub-glub noise",
        tags={"jacuzzi", "water", "comedy"},
    ),
    "overflow": Problem(
        id="overflow",
        cause="too much eager water",
        effect="the jacuzzi splashed over the rim",
        location="jacuzzi",
        risk="the towels got soggy",
        fix="turn down the valve",
        clue="the water climbed the sides like it wanted a snack",
        tags={"jacuzzi", "pipe", "water", "comedy"},
    ),
}

TOOLS = {
    "wrench": Tool(
        id="wrench",
        label="wrench",
        phrase="a shiny little wrench",
        solves={"leak"},
        use_verb="tightened",
        funny_finish="clicked with a proud little twang",
        tags={"pipe", "repair"},
    ),
    "plunger": Tool(
        id="plunger",
        label="plunger",
        phrase="a red plunger",
        solves={"clog"},
        use_verb="pushed",
        funny_finish="made one loud boing and then behaved",
        tags={"jacuzzi", "repair"},
    ),
    "valve_key": Tool(
        id="valve key",
        label="valve key",
        phrase="a brass valve key",
        solves={"overflow"},
        use_verb="turned",
        funny_finish="gave a tiny squeak like a mouse in shoes",
        tags={"pipe", "jacuzzi", "repair"},
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Theo", "Ava", "Eli", "Zoe", "Ben"]
GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["curious", "kind", "cheerful", "silly", "careful", "brave"]
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            if prob.location in setting.affords:
                for tool_id, tool in TOOLS.items():
                    if prob_id in tool.solves:
                        out.append((place, prob_id, tool_id))
    return out


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not reasonably solve the {problem.id} problem. "
        f"The comedy needs a real fix, not a pretend one.)"
    )


def setting_intro(setting: Setting, problem: Problem) -> str:
    if problem.id == "leak":
        return f"{setting.place.capitalize()} smelled faintly of soap and wet tile."
    if problem.id == "clog":
        return f"{setting.place.capitalize()} looked cozy, but the water was making a rude little face."
    return f"{setting.place.capitalize()} was ready for a ridiculous plumbing surprise."


def _do_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    if problem.id == "leak":
        actor.meters["wetness"] = actor.meters.get("wetness", 0.0) + 1
        actor.memes["alarm"] = actor.memes.get("alarm", 0.0) + 1
    elif problem.id == "clog":
        actor.meters["mess"] = actor.meters.get("mess", 0.0) + 1
        actor.memes["annoyance"] = actor.memes.get("annoyance", 0.0) + 1
    elif problem.id == "overflow":
        actor.meters["wetness"] = actor.meters.get("wetness", 0.0) + 1
        actor.memes["panic"] = actor.memes.get("panic", 0.0) + 1
    if narrate:
        world.say(problem.effect + ".")


def predict_fix(world: World, tool: Tool, problem: Problem) -> bool:
    return problem.id in tool.solves


def character_intro(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.get('traits', [])), 'bright')} "
        f"{hero.type} who liked making even boring days funny."
    )
    world.say(
        f"{hero.id} lived with {parent.label_word} and loved checking the pipes and jacuzzi "
        f"when they made strange noises."
    )
    world.say(setting_intro(world.setting, problem))


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"joy": 0.0, "curiosity": 1.0, "traits": [params.trait]},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={},
        memes={"calm": 1.0},
    ))
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]

    pipe = world.add(Entity(
        id="Pipe",
        type="pipe",
        label="pipe",
        phrase="the little pipe under the sink",
        location="pipe",
        meters={"drip": 0.0, "looseness": 0.0},
        memes={"irritation": 1.0},
    ))
    jacuzzi = world.add(Entity(
        id="Jacuzzi",
        type="jacuzzi",
        label="jacuzzi",
        phrase="the bubbly jacuzzi",
        location="jacuzzi",
        meters={"water": 0.0, "noise": 0.0},
        memes={"mood": 0.0},
    ))
    world.facts.update(hero=hero, parent=parent, problem=problem, tool=tool, pipe=pipe, jacuzzi=jacuzzi)

    character_intro(world, hero, parent, problem)
    world.para()
    world.say(
        f"Then {hero.id} heard the {problem.location} go {problem.clue}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} pointed at the problem and said, "
        f"\"Well, that is not a spa sound.\""
    )

    # Middle: recognize the problem.
    if problem.id == "leak":
        pipe.meters["looseness"] += 1
    elif problem.id == "clog":
        jacuzzi.meters["water"] += 1
        jacuzzi.memes["mood"] -= 1
    else:
        pipe.meters["looseness"] += 1
        jacuzzi.meters["water"] += 1

    world.para()
    world.say(
        f"{hero.id} looked at {tool.phrase} and decided to help instead of pretending the noise was normal."
    )
    if not predict_fix(world, tool, problem):
        raise StoryError(explain_rejection(problem, tool))

    # Resolution
    world.say(
        f"{hero.id} used {tool.phrase} to {tool.use_verb} the {problem.location}."
    )
    world.say(
        f"{tool.label.capitalize()} {tool.funny_finish}."
    )
    if problem.id == "leak":
        pipe.meters["looseness"] = 0.0
        pipe.meters["drip"] = 0.0
        hero.meters["wetness"] = 0.0
        world.say("The drips stopped, and the bathroom got quiet enough to hear a happy sigh.")
    elif problem.id == "clog":
        jacuzzi.meters["water"] = 0.0
        jacuzzi.memes["mood"] = 1.0
        world.say("The bubbles came back in a cheerful pop-pop-pop, like the jacuzzi had remembered how to smile.")
    else:
        pipe.meters["looseness"] = 0.0
        jacuzzi.meters["water"] = 0.0
        world.say("The water settled down, the floor stayed dry, and the jacuzzi behaved like a polite bathtub with big dreams.")

    hero.memes["joy"] += 2.0
    parent.memes["calm"] += 1.0
    world.say(
        f"{hero.id} grinned because doing the honest fix felt better than making excuses."
    )
    world.say(
        f"In the end, {hero.id} and {parent.label_word} laughed at the silly plumbing mystery and left the room neat and peaceful."
    )

    world.facts.update(
        resolved=True,
        happy_ending=True,
        moral_value=True,
        place=params.place,
        seed=params.seed,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        f'Write a short comedy story for a child about a {problem.location} problem, a {tool.label}, and a kind fix.',
        f"Tell a funny story where {hero.id} notices a {problem.location} problem and solves it honestly.",
        f"Write a happy-ending story about a pipe and a jacuzzi that sound silly until someone repairs them.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    problem = f["problem"]
    tool = f["tool"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"What problem did {hero.id} notice in {place}?",
            answer=f"{hero.id} noticed a {problem.id} problem with the {problem.location}. The {problem.clue} showed that something was wrong.",
        ),
        QAItem(
            question=f"What did {hero.id} use to fix the {problem.location}?",
            answer=f"{hero.id} used {tool.phrase} to help solve the problem. That was the right tool for this silly job.",
        ),
        QAItem(
            question=f"Why was {hero.id} being helpful a good choice?",
            answer=f"Being helpful was a good choice because it fixed the problem instead of ignoring it. The house got calmer, and everyone could enjoy the room again.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label_word} feel at the end?",
            answer=f"They felt happy and relieved. The joke of the story was over, and the room ended peaceful and clean.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem = f["problem"]
    tool = f["tool"]
    out = []
    if "pipe" in problem.tags or "pipe" in tool.tags:
        out.append(QAItem(
            question="What is a pipe for?",
            answer="A pipe is a tube that carries water from one place to another, like a hallway for water.",
        ))
    if "jacuzzi" in problem.tags or "jacuzzi" in tool.tags:
        out.append(QAItem(
            question="What is a jacuzzi?",
            answer="A jacuzzi is a tub with warm water and bubbles that can feel relaxing and fancy.",
        ))
    if "repair" in tool.tags:
        out.append(QAItem(
            question="Why do people use tools when something is broken?",
            answer="People use tools because tools help them fix things safely and carefully instead of making the problem worse.",
        ))
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_with_location(P, L) :- problem(P), location(P, L).
solves(T, P) :- tool(T), problem(P), matches(T, P).

valid_story(Place, Prob, Tool) :-
    setting(Place),
    affords(Place, Loc),
    problem(Prob),
    location(Prob, Loc),
    tool(Tool),
    solves(Tool, Prob).
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
        lines.append(asp.fact("location", pid, p.location))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for s in sorted(t.solves):
            lines.append(asp.fact("matches", tid, s))
        for tg in sorted(t.tags):
            lines.append(asp.fact("tool_tag", tid, tg))
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
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld: pipe + jacuzzi + problem solving + happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--name")
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, prob_id, tool_id = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(GENDERS)
    parent = args.parent or rng.choice(PARENT_TYPES)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=prob_id, tool=tool_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.location:
                bits.append(f"location={e.location}")
            print(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for place, prob, tool in combos:
            print(f"  {place:10} {prob:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("bathroom", "leak", "wrench", "Mia", "girl", "mother", "curious", base_seed),
            StoryParams("spa", "clog", "plunger", "Noah", "boy", "father", "silly", base_seed),
            StoryParams("basement", "leak", "wrench", "Ava", "girl", "mother", "careful", base_seed),
            StoryParams("bathroom", "overflow", "valve_key", "Theo", "boy", "father", "brave", base_seed),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.problem} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
