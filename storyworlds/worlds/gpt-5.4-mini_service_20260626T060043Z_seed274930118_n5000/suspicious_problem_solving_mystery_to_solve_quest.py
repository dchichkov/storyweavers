#!/usr/bin/env python3
"""
A standalone storyworld for a small space-adventure mystery quest.

Premise:
- A crew is sent to solve a suspicious problem on a tiny station or moon base.
- They investigate clues, choose a tool, and complete a quest by fixing the issue.
- The story is state-driven: suspicion rises from evidence, then drops when the
  real cause is found and repaired.

This world keeps the prose child-facing and concrete, with a clear setup,
mystery, problem-solving middle, and a satisfying ending image.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Problem:
    id: str
    noun: str
    suspicious_signs: list[str]
    true_cause: str
    fix: str
    quest_objective: str
    danger: str
    clue_nouns: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_against: set[str]
    why: str


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    role: str
    partner: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trail: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trail.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "station": Setting(
        place="the star station",
        detail="Its silver halls hummed softly, and bright windows looked out at the stars.",
    ),
    "moonbase": Setting(
        place="the moon base",
        detail="Its dome was tucked under a pale sky, with dusty paths and blinking lamps.",
    ),
    "dock": Setting(
        place="the dock hangar",
        detail="Big cargo doors stood open, and small ships slept beside glowing fuel lines.",
    ),
}

PROBLEMS = {
    "signal": Problem(
        id="signal",
        noun="signal",
        suspicious_signs=["a blinking light kept turning red", "the radio made fuzzy sounds"],
        true_cause="a tiny scratch on the relay lens",
        fix="polish the relay lens clean",
        quest_objective="restore the lost message",
        danger="the crew might miss an urgent map clue",
        clue_nouns={"relay", "radio", "lens"},
        tags={"signal", "radio", "lens", "mystery"},
    ),
    "door": Problem(
        id="door",
        noun="door",
        suspicious_signs=["a hatch kept clicking open and shut", "dust moved in little lines near the seam"],
        true_cause="a pebble stuck in the hatch track",
        fix="lift the pebble out with a magnet",
        quest_objective="seal the hatch",
        danger="air could slip out into space",
        clue_nouns={"hatch", "track", "pebble"},
        tags={"door", "hatch", "pebble", "mystery"},
    ),
    "drift": Problem(
        id="drift",
        noun="drift",
        suspicious_signs=["a crate floated the wrong way", "the floor map arrows did not match the route"],
        true_cause="a broken thruster vent pushing air sideways",
        fix="patch the vent with a spare seal",
        quest_objective="stabilize the cargo bay",
        danger="boxes could bump into everything",
        clue_nouns={"crate", "thruster", "vent"},
        tags={"drift", "thruster", "vent", "mystery"},
    ),
}

TOOLS = [
    Tool(
        id="scanner",
        label="a pocket scanner",
        phrase="a pocket scanner with a bright blue screen",
        helps_against={"signal", "radio", "lens", "mystery"},
        why="it could spot tiny marks and hidden clues",
    ),
    Tool(
        id="magnet",
        label="a hand magnet",
        phrase="a small hand magnet",
        helps_against={"door", "hatch", "pebble"},
        why="it could lift out metal bits without hurting anything",
    ),
    Tool(
        id="seal",
        label="a spare seal patch",
        phrase="a spare seal patch and a roll of tape",
        helps_against={"drift", "vent"},
        why="it could cover a leaking place and stop the air push",
    ),
]

CREW_ROLES = ["captain", "pilot", "mechanic", "scout"]
PARTNERS = ["pilot", "mechanic", "scout", "captain"]
NAMES = ["Nova", "Rin", "Tess", "Milo", "Ari", "Pip", "Luna", "Jett"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is suspicious when one of its signs is observed.
suspicious(P) :- sign(P, _).

% A tool helps a problem only if it matches the problem's clue family.
can_fix(T, P) :- tool(T), problem(P), helps(T, P).

% A story is valid when the setting contains the problem, the mystery is
% suspicious, and there is at least one tool that can fix it.
valid_story(S, P) :- setting(S), problem(P), in_setting(S, P), suspicious(P), can_fix(_, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("noun", pid, p.noun))
        lines.append(asp.fact("in_setting", "station", pid) if pid == "signal" else "")
        lines.append(asp.fact("in_setting", "moonbase", pid) if pid == "door" else "")
        lines.append(asp.fact("in_setting", "dock", pid) if pid == "drift" else "")
        for sign in p.suspicious_signs:
            lines.append(asp.fact("sign", pid, sign))
        for n in sorted(p.clue_nouns):
            lines.append(asp.fact("clue", pid, n))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for tag in sorted(t.helps_against):
            lines.append(asp.fact("helps", t.id, tag))
    return "\n".join([x for x in lines if x])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    python_set = set()
    for place, setting in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            if place == "station" and pid == "signal":
                if any(t.helps_against & p.tags for t in TOOLS):
                    python_set.add((place, pid))
            if place == "moonbase" and pid == "door":
                if any(t.helps_against & p.tags for t in TOOLS):
                    python_set.add((place, pid))
            if place == "dock" and pid == "drift":
                if any(t.helps_against & p.tags for t in TOOLS):
                    python_set.add((place, pid))

    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python reasonableness ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if tool.helps_against & problem.tags:
            return tool
    return None


def reasonableness_check(place: str, problem: Problem) -> bool:
    if place == "station" and problem.id == "signal":
        return choose_tool(problem) is not None
    if place == "moonbase" and problem.id == "door":
        return choose_tool(problem) is not None
    if place == "dock" and problem.id == "drift":
        return choose_tool(problem) is not None
    return False


def explain_rejection(place: str, problem: Problem) -> str:
    return (
        f"(No story: the choice of {place} and the {problem.noun} problem does not "
        f"fit this world's careful mystery rules.)"
    )


def setup_story(world: World, hero: Entity, partner: Entity, problem: Problem) -> None:
    hero.memes["curiosity"] = 1.0
    hero.memes["duty"] = 1.0
    world.say(
        f"{hero.id} was a {hero.type} on {world.setting.place} who loved solving strange problems."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {partner.id} were on a quest to fix a suspicious {problem.noun}."
    )


def introduce_mystery(world: World, problem: Problem) -> None:
    world.para()
    world.say(
        f"Inside {world.setting.place}, something felt wrong. {problem.suspicious_signs[0].capitalize()}."
    )
    world.say(problem.suspicious_signs[1].capitalize() + ".")
    world.facts["suspicion"] = True


def investigate(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["suspicion"] = 1.0
    world.say(
        f"{hero.id} squinted at the clues and said, \"This is a mystery to solve.\""
    )
    world.say(
        f"{hero.pronoun().capitalize()} looked for a pattern in the {problem.clue_nouns.pop() if problem.clue_nouns else problem.noun}."
    )


def use_tool(world: World, hero: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["confidence"] = 1.0
    world.para()
    world.say(
        f"{hero.id} picked up {tool.label} because {tool.why}."
    )
    world.say(
        f"It was the right tool for the quest, and {hero.pronoun('possessive')} hands moved carefully."
    )


def solve_problem(world: World, hero: Entity, partner: Entity, problem: Problem, tool: Tool) -> None:
    hero.memes["joy"] = 1.0
    world.para()
    world.say(
        f"At last, {hero.id} found the true cause: {problem.true_cause}."
    )
    world.say(
        f"Together, {hero.id} and {partner.id} used {tool.label} to {problem.fix}."
    )
    world.say(
        f"The suspicious feeling faded, and the quest became a success because {problem.quest_objective}."
    )
    world.say(
        f"Now the station felt calm again, with a clean shining part where the trouble had been."
    )
    world.facts["resolved"] = True
    world.facts["cause"] = problem.true_cause
    world.facts["fix"] = problem.fix


def tell(setting: Setting, problem: Problem, name: str, role: str, partner_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=role))
    partner = world.add(Entity(id=partner_role.capitalize(), kind="character", type=partner_role))

    setup_story(world, hero, partner, problem)
    introduce_mystery(world, problem)
    investigate(world, hero, problem)
    tool = choose_tool(problem)
    if tool is None:
        raise StoryError(explain_rejection(setting.place, problem))
    use_tool(world, hero, problem, tool)
    solve_problem(world, hero, partner, problem, tool)

    world.facts.update(
        hero=hero,
        partner=partner,
        problem=problem,
        tool=tool,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    return [
        f'Write a short space-adventure story for a young child about a suspicious {problem.noun} that needs solving.',
        f'Tell a mystery-to-solve quest where {hero.id} and a helper fix the strange problem on {world.setting.place}.',
        f'Write a gentle space story that ends with a clever repair and a calm ship, using the word "suspicious".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    problem = f["problem"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What kind of story is this one?",
            answer=f"It is a space adventure about a suspicious {problem.noun}, a mystery to solve, and a quest to fix it.",
        ),
        QAItem(
            question=f"Who solved the problem on {world.setting.place}?",
            answer=f"{hero.id} solved it with help from {partner.id}. They worked together like a small crew.",
        ),
        QAItem(
            question=f"What tool helped {hero.id} fix the trouble?",
            answer=f"{tool.label.capitalize()} helped because it was the right tool for the clue and the repair.",
        ),
        QAItem(
            question=f"What was the true cause of the strange problem?",
            answer=f"The real cause was {f['cause']}. That was the clue that explained why the trouble looked suspicious.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a scanner do?",
            answer="A scanner helps you look closely at small details and hidden marks.",
        ),
        QAItem(
            question="Why is a mystery something to solve?",
            answer="A mystery is something puzzling, so people ask questions and search for clues until they understand it.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that asks someone to travel, try hard, and solve a problem.",
        ),
        QAItem(
            question="Why do people use tools carefully in space?",
            answer="People use tools carefully so they can fix things without causing more trouble.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind:8}) type={e.type}")
        if e.memes:
            lines.append(f"    memes={dict(e.memes)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="station", problem="signal", name="Nova", role="girl", partner="mechanic"),
    StoryParams(place="moonbase", problem="door", name="Rin", role="boy", partner="captain"),
    StoryParams(place="dock", problem="drift", name="Tess", role="girl", partner="pilot"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery quest storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=PARTNERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or {"station": "signal", "moonbase": "door", "dock": "drift"}[place]
    prob = PROBLEMS[problem]
    if not reasonableness_check(place, prob):
        raise StoryError(explain_rejection(place, prob))
    role = args.role or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice(PARTNERS)
    return StoryParams(place=place, problem=problem, name=name, role=role, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], params.name, params.role, params.partner)
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


# ---------------------------------------------------------------------------
# Main / CLI
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        atoms = asp.atoms(model, "valid_story")
        print(f"{len(atoms)} valid story combinations:")
        for place, problem in atoms:
            print(f"  {place} {problem}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
