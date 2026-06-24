#!/usr/bin/env python3
"""
A small mythic story world about a curious star-seeker, a problem that skews
the sky-signs, and a careful repair that restores the path.

The seed image:
---
In an old myth, a child could read the night sky like a map. One evening, an
asterisk-shaped sign appeared in the clouds, but the sign was skewed, and the
way to the river shrine no longer looked clear. The child asked many questions,
found the cause of the skew, and solved it with a simple, brave fix.
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
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
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
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    description: str
    symptom: str
    cause: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "temple": Setting(place="the temple hill", mood="golden", affords={"read_sign", "climb", "repair"}),
    "courtyard": Setting(place="the stone courtyard", mood="echoing", affords={"read_sign", "repair"}),
    "riverbank": Setting(place="the riverbank shrine", mood="misty", affords={"read_sign", "repair"}),
}

PROBLEMS = {
    "skewed_sign": Problem(
        id="skewed_sign",
        description="the sky-sign tilts sideways",
        symptom="the asterisk mark in the clouds points the wrong way",
        cause="a wind-knot bent the hanging cord",
        fix_hint="straighten the cord and retie it",
        tags={"asterisk", "skew", "curiosity", "problem_solving"},
    ),
    "dark_path": Problem(
        id="dark_path",
        description="the path to the shrine is hard to follow",
        symptom="the stones look like they turn in circles",
        cause="the lantern bowl has gone dim",
        fix_hint="light the lantern bowl again",
        tags={"curiosity", "problem_solving"},
    ),
}

TOOLS = {
    "cord": Tool(
        id="cord",
        label="a bright cord",
        phrase="a bright cord with a small knot",
        use="straighten and retie the sign",
        guards={"skew"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a bronze lantern",
        phrase="a bronze lantern with a clear glass bowl",
        use="bring back the light",
        guards={"dark"},
    ),
    "stick": Tool(
        id="stick",
        label="a long reed stick",
        phrase="a long reed stick",
        use="point out the true path",
        guards={"curiosity"},
    ),
}

NAMES = ["Ari", "Mira", "Suri", "Niko", "Tala", "Ivo", "Lena", "Pax"]
TITLES = ["child", "boy", "girl", "young pilgrim", "young seeker"]
GUARDIANS = ["mother", "father", "aunt", "uncle", "priestess", "priest"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    hero_type: str
    guardian: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
class Narrative:
    def __init__(self, world: World) -> None:
        self.world = world

    def introduce(self, hero: Entity, guardian: Entity, problem: Problem) -> None:
        self.world.say(
            f"Long ago, in {self.world.setting.place}, there was a little {hero.type} named {hero.id} "
            f"who loved to ask questions about every sign in the sky."
        )
        self.world.say(
            f"{hero.pronoun().capitalize()} and {guardian.label} kept watch over the shrine, "
            f"where {problem.description}."
        )
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
        guardian.memes["care"] = guardian.memes.get("care", 0) + 1

    def omen(self, hero: Entity, problem: Problem) -> None:
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
        self.world.say(
            f"One evening, {hero.id} saw the asterisk mark in the clouds, but it had been skewed by the wind."
        )
        self.world.say(
            f"The sign did not point cleanly to the shrine path, and that made {hero.id} frown."
        )
        hero.meters["confusion"] = hero.meters.get("confusion", 0) + 1

    def question(self, hero: Entity, problem: Problem) -> None:
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
        self.world.say(
            f"{hero.id} asked, \"Why is the asterisk leaning sideways, and what is hiding the true way?\""
        )
        self.world.say(
            f"That question was not foolish; it was the first step toward solving the problem."
        )

    def search(self, hero: Entity, guardian: Entity, problem: Problem, tool: Tool) -> None:
        hero.memes["problem_solving"] = hero.memes.get("problem_solving", 0) + 1
        self.world.say(
            f"Together, {hero.id} and {guardian.label} followed the sign's shadow to find the cause."
        )
        if problem.id == "skewed_sign":
            self.world.say(
                f"They found a wind-knot in the cord, tight as a small fist, and {tool.label} beside the altar."
            )
        else:
            self.world.say(
                f"They found the lantern bowl dim and dusty, waiting for a careful hand."
            )

    def fix(self, hero: Entity, guardian: Entity, problem: Problem, tool: Tool) -> None:
        hero.memes["problem_solving"] = hero.memes.get("problem_solving", 0) + 1
        hero.meters["skill"] = hero.meters.get("skill", 0) + 1
        if problem.id == "skewed_sign":
            self.world.say(
                f"{hero.id} used {tool.label} to straighten the cord and retie it with a steady tug."
            )
            self.world.say(
                f"The asterisk in the clouds stopped skidding sideways and became a clear sign again."
            )
        else:
            self.world.say(
                f"{hero.id} polished the lantern glass and lit the bowl until the path glowed softly."
            )
            self.world.say(
                f"The stones no longer looked like a circle, and the way to the shrine came back into sight."
            )
        guardian.memes["pride"] = guardian.memes.get("pride", 0) + 1

    def ending(self, hero: Entity, guardian: Entity, problem: Problem, tool: Tool) -> None:
        self.world.say(
            f"In the end, {hero.id} stood beneath the sky where the asterisk shone true, and the shrine path was clear."
        )
        self.world.say(
            f"{guardian.label} smiled, because a curious heart and a careful answer had solved what the wind had skewed."
        )


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem is relevant when the setting affords the kind of action needed.
relevant(P,S) :- problem(P), setting(S), needs(P,A), affords(S,A).

% A tool is a valid fix when it guards the symptom kind and matches the problem.
fix(T,P) :- tool(T), problem(P), requires(P,R), guards(T,R).

valid_story(S,P,T) :- relevant(P,S), fix(T,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, "repair"))
        if "skew" in p.tags:
            lines.append(asp.fact("requires", pid, "skew"))
        if "dark" in p.tags:
            lines.append(asp.fact("requires", pid, "dark"))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    left = set(valid_combos())
    right = set((s, p, t) for (s, p, t) in asp_valid_stories())
    if left == right:
        print(f"OK: clingo gate matches valid_combos() ({len(left)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if left - right:
        print("  only in python:", sorted(left - right))
    if right - left:
        print("  only in clingo:", sorted(right - left))
    return 1


# ---------------------------------------------------------------------------
# Constraint logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if "repair" not in setting.affords:
                continue
            for tid, tool in TOOLS.items():
                if problem.id == "skewed_sign" and "skew" in tool.guards:
                    combos.append((sid, pid, tid))
                elif problem.id == "dark_path" and "dark" in tool.guards:
                    combos.append((sid, pid, tid))
    return combos

def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit {problem.description}. "
        f"The fix has to answer the real cause, not only look clever.)"
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.guardian, label=f"the {params.guardian}"))
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world.facts.update(hero=hero, guardian=guardian, problem=problem, tool=tool)

    n = Narrative(world)
    n.introduce(hero, guardian, problem)
    world.para()
    n.omen(hero, problem)
    n.question(hero, problem)
    world.para()
    n.search(hero, guardian, problem, tool)
    n.fix(hero, guardian, problem, tool)
    world.para()
    n.ending(hero, guardian, problem, tool)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, problem, tool = f["hero"], f["problem"], f["tool"]
    return [
        f'Write a myth-like story for a child named {hero.id} about an asterisk sign that becomes skewed and then repaired.',
        f"Tell a gentle myth where {hero.id} notices {problem.description} and uses {tool.label} to solve it.",
        "Write a short, ancient-feeling story about curiosity, problem solving, and a sky-sign that points the wrong way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guardian, problem, tool = f["hero"], f["guardian"], f["problem"], f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} notice in the sky?",
            answer="They noticed an asterisk-shaped sign in the clouds, but it was skewed sideways by the wind.",
        ),
        QAItem(
            question=f"Why did {hero.id} ask questions instead of ignoring the sign?",
            answer=f"{hero.id} was curious, so they wanted to understand why the sign looked wrong and what was causing the trouble.",
        ),
        QAItem(
            question=f"How did {hero.id} and {guardian.label} fix the problem?",
            answer=f"They found the cause and used {tool.label} to straighten the sign again, which solved the problem.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer="The skew disappeared, the asterisk became clear again, and the path to the shrine was easy to follow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an asterisk?",
            answer="An asterisk is a small star-shaped mark used in writing or signs.",
        ),
        QAItem(
            question="What does skew mean?",
            answer="Skew means tilted or slanted to one side instead of standing straight.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, ask questions, and find out why something is happening.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking for the cause of a trouble and choosing a good way to fix it.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="temple", problem="skewed_sign", tool="cord", name="Ari", hero_type="child", guardian="priestess"),
    StoryParams(place="courtyard", problem="skewed_sign", tool="cord", name="Mira", hero_type="girl", guardian="mother"),
    StoryParams(place="riverbank", problem="dark_path", tool="lantern", name="Tala", hero_type="young seeker", guardian="father"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: curiosity, problem solving, and a skewed asterisk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=GUARDIANS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    hero_type = args.gender or rng.choice(TITLES)
    guardian = args.parent or rng.choice(GUARDIANS)
    if args.tool and args.problem and (place, problem, tool) not in valid_combos():
        raise StoryError(explain_rejection(PROBLEMS[problem], TOOLS[tool]))
    return StoryParams(place=place, problem=problem, tool=tool, name=name, hero_type=hero_type, guardian=guardian)


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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (setting, problem, tool) combos:\n")
        for s, p, t in stories:
            print(f"  {s:10} {p:14} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.name}: {p.problem} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
