#!/usr/bin/env python3
"""
A standalone story world for a small superhero-style tale on a steep hill path.

Premise:
- A curious child hero walks a steep hill path with a special kaleidoscope.
- A problem appears: something important is lost or blocked on the path.
- The hero uses sincere teamwork and problem solving to fix it.

The world is intentionally tiny and constraint-checked: every generated story
comes from a simulated state, not from a frozen paragraph with swapped nouns.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "stuck": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "sincerity": 0.0, "hope": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    path_steep: bool = True
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        import copy as _copy
        w = World(self.setting, self.path_steep)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    result: str
    risk: str
    tag: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    helps_with: set[str]


@dataclass
class StoryParams:
    name: str
    gender: str
    sidekick: str
    problem: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PROBLEMS = {
    "stuck_sign": Problem(
        id="stuck_sign",
        label="a stuck warning sign",
        verb="free the warning sign",
        result="the sign could point the way again",
        risk="the path could stay confusing",
        tag="help",
    ),
    "fallen_gate": Problem(
        id="fallen_gate",
        label="a fallen gate",
        verb="lift the fallen gate",
        result="the path could open again",
        risk="people could not get through",
        tag="repair",
    ),
    "lost_compass": Problem(
        id="lost_compass",
        label="a lost compass",
        verb="find the compass",
        result="the way could be clear",
        risk="the climb could go the wrong way",
        tag="find",
    ),
}

TOOLS = {
    "kaleidoscope": Tool(
        id="kaleidoscope",
        label="a kaleidoscope",
        phrase="a bright kaleidoscope",
        solves={"focus", "find"},
        helps_with={"find", "clue"},
    ),
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="a strong rope",
        solves={"repair", "lift"},
        helps_with={"repair", "lift"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a small lantern",
        solves={"find", "focus"},
        helps_with={"find", "light"},
    ),
}

NAMES = ["Ava", "Mia", "Leo", "Finn", "Noah", "Zoe", "Nora", "Eli"]
SIDEKICKS = ["rookie helper", "young scout", "brave friend", "tiny teammate"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combo(problem: Problem, tool: Tool) -> bool:
    if problem.id == "lost_compass":
        return "find" in tool.solves
    if problem.id == "fallen_gate":
        return "repair" in tool.solves
    if problem.id == "stuck_sign":
        return "find" in tool.helps_with or "focus" in tool.helps_with
    return False


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, p in PROBLEMS.items():
        for tid, t in TOOLS.items():
            if valid_combo(p, t):
                out.append((pid, tid))
    return out


def setting_detail() -> str:
    return "The steep hill path curled upward between rocks and wind-bent grass."


def predict(world: World, hero: Entity, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    apply_action(sim, hero.id, problem, tool, narrate=False)
    return {
        "fixed": bool(sim.facts.get("fixed")),
        "resolved": bool(sim.facts.get("resolved")),
    }


def apply_action(world: World, hero_id: str, problem: Problem, tool: Tool, narrate: bool = True) -> None:
    if ("action", problem.id, tool.id) in world.fired:
        return
    world.fired.add(("action", problem.id, tool.id))
    hero = world.get(hero_id)
    if problem.id == "lost_compass" and tool.id in {"kaleidoscope", "lantern"}:
        hero.memes["curiosity"] += 1
        world.facts["fixed"] = True
    elif problem.id == "fallen_gate" and tool.id == "rope":
        hero.memes["resolve"] += 1
        world.facts["fixed"] = True
    elif problem.id == "stuck_sign" and tool.id in {"kaleidoscope", "lantern"}:
        hero.memes["curiosity"] += 1
        world.facts["fixed"] = True
    else:
        world.facts["fixed"] = False

    if world.facts.get("fixed"):
        world.facts["resolved"] = True
        if narrate:
            world.say(f"The plan worked, and {problem.result}.")
    elif narrate:
        world.say(f"The first try did not work, and the problem stayed on the hill.")


def tell_world(params: StoryParams) -> World:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")

    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if not valid_combo(problem, tool):
        raise StoryError("That tool cannot reasonably solve that problem.")

    world = World("steep hill path")
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    sidekick = world.add(Entity(id="Sidekick", kind="character", type="friend", label=params.sidekick))
    item = world.add(Entity(
        id="tool",
        type=tool.id,
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
        worn_by=hero.id,
    ))
    problem_item = world.add(Entity(
        id="problem",
        type=problem.id,
        label=problem.label,
        phrase=problem.label,
        caretaker=sidekick.id,
    ))

    hero.memes["curiosity"] += 1
    hero.memes["sincerity"] += 1

    world.say(f"{hero.id} was a small hero with a sincere heart and a curious mind.")
    world.say(f"{hero.id} carried {item.phrase} on the steep hill path.")
    world.say(setting_detail())
    world.say(f"Then {hero.id} and {sidekick.label} noticed {problem_item.label}.")
    world.say(f"The problem made the climb feel harder because {problem.risk}.")

    world.para()
    world.say(f"{hero.id} looked closely and thought like a superhero.")
    world.say(f"With a sincere promise to help, {hero.id} tried {tool.label} for the job.")
    apply_action(world, hero.id, problem, tool, narrate=True)

    world.para()
    if world.facts.get("resolved"):
        world.say(f"{hero.id} used careful problem solving instead of rushing.")
        if problem.id == "lost_compass":
            world.say(f"The kaleidoscope caught the light, and its shining patterns helped {hero.id} spot the lost compass under the stones.")
        elif problem.id == "stuck_sign":
            world.say(f"The kaleidoscope’s bright colors helped {hero.id} notice the exact twist needed to free the sign.")
        else:
            world.say(f"The rope gave the team enough strength to lift the fallen gate together.")
        world.say(f"In the end, {problem.result}, and the steep hill path felt friendly again.")
    else:
        world.say(f"{hero.id} tried hard, but the answer was not there yet.")

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        problem=problem,
        tool=tool,
        item=item,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story for a child on a steep hill path that includes the word "kaleidoscope".',
        f"Tell a sincere superhero story where {f['hero'].id} uses problem solving to help with {f['problem'].label}.",
        'Write a gentle action story about curiosity, a steep hill path, and a clever tool.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    sidekick: Entity = f["sidekick"]
    return [
        QAItem(
            question=f"Who is the hero in the story?",
            answer=f"{hero.id} is the hero, and {sidekick.label} is the helper friend on the steep hill path.",
        ),
        QAItem(
            question=f"What problem did they find?",
            answer=f"They found {problem.label} on the steep hill path, and it made the climb harder.",
        ),
        QAItem(
            question=f"What tool did {hero.id} carry?",
            answer=f"{hero.id} carried {tool.phrase}, which helped with the problem.",
        ),
        QAItem(
            question=f"How did the hero solve the trouble?",
            answer=f"{hero.id} used sincere problem solving and the tool to help fix {problem.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kaleidoscope?",
            answer="A kaleidoscope is a tube with mirrors and colored pieces that makes pretty changing patterns when you look through it.",
        ),
        QAItem(
            question="What does sincere mean?",
            answer="Sincere means honest and real, with feelings that are true and not pretend.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and trying ideas to fix a hard situation.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more and look closely at how things work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem_tool(P,T) :- problem(P), tool(T), compatible(P,T).
compatible(lost_compass,kaleidoscope).
compatible(lost_compass,lantern).
compatible(fallen_gate,rope).
compatible(stuck_sign,kaleidoscope).
compatible(stuck_sign,lantern).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for pid, tid in valid_combos():
        lines.append(asp.fact("compatible", pid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show problem_tool/2."))
    return sorted(set(asp.atoms(model, "problem_tool")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} combos.")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld on a steep hill path.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.problem and args.tool:
        if (args.problem, args.tool) not in combos:
            raise StoryError("That problem and tool do not fit together.")
    choices = [
        (p, t) for p, t in combos
        if (not args.problem or p == args.problem)
        and (not args.tool or t == args.tool)
    ]
    if not choices:
        raise StoryError("No valid story matches those options.")
    pid, tid = rng.choice(choices)
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(name=name, gender=gender, sidekick=sidekick, problem=pid, tool=tid)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show problem_tool/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, t in asp_valid_combos():
            print(p, t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(StoryParams(name="Ava", gender="girl", sidekick="brave friend", problem=p, tool=t))
                   for p, t in valid_combos()]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50 + 50:
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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
