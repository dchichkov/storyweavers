#!/usr/bin/env python3
"""
storyworlds/worlds/willow_seven_problem_solving_lesson_learned_comedy.py
========================================================================

A tiny comedy storyworld built from the seed words "willow" and "seven".

Premise:
- Willow is a small character who wants to do something cheerful.
- Seven little items/companions create a comic problem.
- Willow tries a sensible fix, learns a lesson, and the ending proves the change.

The world is intentionally small and constraint-driven:
- Problems are concrete and stateful.
- The turn is a real simulated change, not a frozen template.
- The lesson learned is encoded in the world state and narrated at the end.
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
# Small world constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "order": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "confusion": 0.0, "confidence": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the willow yard"
    mood: str = "bright"


@dataclass
class Problem:
    id: str
    label: str
    verb: str
    mess: str
    fix_hint: str
    zone: str
    comic: str
    lesson: str


@dataclass
class Tool:
    id: str
    label: str
    fixs: set[str]
    zone: str
    phrase: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    seed: Optional[int] = None


SCENES = {
    "yard": Scene(place="the willow yard", mood="bright"),
    "garden": Scene(place="the small garden", mood="breezy"),
    "porch": Scene(place="the front porch", mood="sunny"),
}

PROBLEMS = {
    "windy_kites": Problem(
        id="windy_kites",
        label="seven kites",
        verb="fly",
        mess="tangled strings",
        fix_hint="sort the strings by color",
        zone="sky",
        comic="they all bumped noses in the air",
        lesson="sometimes a messy problem gets easier when you slow down and sort it out",
    ),
    "sticky_pies": Problem(
        id="sticky_pies",
        label="seven pies",
        verb="carry",
        mess="squished filling",
        fix_hint="put the pies on a tray",
        zone="hands",
        comic="one pie kept wobbling like a sleepy jelly",
        lesson="sometimes the smartest fix is a steadier way to hold things",
    ),
    "silly_shoes": Problem(
        id="silly_shoes",
        label="seven shoes",
        verb="line up",
        mess="crooked rows",
        fix_hint="match left shoes with left shoes",
        zone="floor",
        comic="the shoes looked like they were dancing in pairs",
        lesson="good problems often need careful matching, not faster running",
    ),
}

TOOLS = {
    "tray": Tool(
        id="tray",
        label="a steady tray",
        fixs={"sticky_pies"},
        zone="hands",
        phrase="put the pies on a steady tray",
        ending="held the tray with both hands",
    ),
    "string_box": Tool(
        id="string_box",
        label="a string box",
        fixs={"windy_kites"},
        zone="sky",
        phrase="lay the strings into a string box in order",
        ending="tucked the strings away in neat loops",
    ),
    "shoe_pairs": Tool(
        id="shoe_pairs",
        label="a pair chart",
        fixs={"silly_shoes"},
        zone="floor",
        phrase="sort the shoes with a pair chart",
        ending="lined the shoes up left with left and right with right",
    ),
}

NAMES = ["Willow", "Mina", "Toby", "Nora", "Eli", "Pippa", "Luca", "Zoe"]
TUNES = ["playful", "curious", "bouncy", "cheerful", "sly", "careful"]


def _do_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    hero.meters["mess"] += 1
    hero.memes["confusion"] += 1
    if narrate:
        world.say(
            f"{hero.id} tried to {problem.verb} the {problem.label}, but {problem.comic}."
        )


def predict_fix(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.fixs


def solve_problem(world: World, hero: Entity, problem: Problem, tool: Tool) -> bool:
    if not predict_fix(problem, tool):
        return False
    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} paused, took a breath, and said, "
        f"\"Let's {tool.phrase}.\""
    )
    world.say(
        f"That worked: {tool.ending}, and the {problem.label} stopped causing a fuss."
    )
    hero.meters["order"] += 1
    hero.memes["lesson"] += 1
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1.0)
    return True


def lesson_line(hero: Entity, problem: Problem) -> str:
    return (
        f"{hero.id} learned that {problem.lesson}. "
        f"After that, {hero.pronoun('subject')} felt proud of the fix instead of flustered."
    )


def tell(scene: Scene, problem: Problem, tool: Tool, name: str = "Willow") -> World:
    world = World(scene)
    hero = world.add(Entity(id=name, kind="character", type="girl"))
    helper = world.add(Entity(id="Helper", kind="character", type="mother"))
    item = world.add(Entity(id=problem.id, type="thing", label=problem.label, plural=True, owner=hero.id))

    world.say(
        f"Willow was a {random.choice(TUNES)} little kid who loved trying big ideas in {scene.place}."
    )
    world.say(
        f"One day, {hero.id} spotted {problem.label} and decided to {problem.verb} them all at once."
    )

    world.para()
    _do_problem(world, hero, problem, narrate=True)
    world.say(
        f"{helper.pronoun().capitalize()} gave a tiny smile and said, "
        f"\"Maybe there is a better way.\""
    )

    world.para()
    solved = solve_problem(world, hero, problem, tool)
    if solved:
        world.say(
            f"In the end, {hero.id} and {helper.pronoun('object')} laughed at the silly trouble together."
        )
        world.say(lesson_line(hero, problem))
    else:
        raise StoryError("No compatible tool exists for this problem.")

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        problem=problem,
        tool=tool,
        solved=solved,
        scene=scene,
    )
    return world


def build_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny short story for a young child about "{f["hero"].id}" and seven small troubles.',
        f"Tell a comedy story where {f['hero'].id} learns to solve a problem with a calmer plan.",
        f"Write a gentle, funny story about {f['problem'].label} and a smart fix that teaches a lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]

    return [
        QAItem(
            question=f"What did {hero.id} first try to do?",
            answer=f"{hero.id} first tried to {problem.verb} the {problem.label}, but it turned into a funny mess.",
        ),
        QAItem(
            question=f"What helped {hero.id} fix the problem?",
            answer=f"{tool.label} helped because it let {hero.id} use a steadier plan instead of rushing.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {problem.lesson}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm?",
            answer=f"{helper.pronoun().capitalize()} helped by suggesting there might be a better way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way that makes the trouble stop or become easier.",
        ),
        QAItem(
            question="Why can being careful help in comedy stories?",
            answer="Being careful can help because a calm plan often fixes the silly trouble without making it worse.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the helpful idea a character understands after the story changes them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_solved(P) :- tool(T), helps(T,P).
lesson_learned(H) :- problem_solved(P), hero(H), problem(P).
compatible_story(P,T) :- problem(P), tool(T), helps(T,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.fixs):
            lines.append(asp.fact("helps", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for pid in PROBLEMS:
        for tid, t in TOOLS.items():
            if pid in t.fixs:
                out.append((pid, tid))
    return sorted(out)


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} compatible pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in Python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy world about Willow and seven things.")
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pairs = valid_pairs()
    if args.problem and args.tool and (args.problem, args.tool) not in pairs:
        raise StoryError("That tool does not solve that problem.")
    choices = [
        (p, t) for (p, t) in pairs
        if (args.problem is None or p == args.problem)
        and (args.tool is None or t == args.tool)
    ]
    if not choices:
        raise StoryError("No valid problem/tool pair matches the requested options.")

    problem, tool = rng.choice(sorted(choices))
    name = args.name or rng.choice(NAMES)
    place = args.place or rng.choice(list(SCENES))
    return StoryParams(place=place, problem=problem, tool=tool, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.place], PROBLEMS[params.problem], TOOLS[params.tool], params.name)
    return StorySample(
        params=params,
        story=build_story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="yard", problem="windy_kites", tool="string_box", name="Willow"),
    StoryParams(place="garden", problem="sticky_pies", tool="tray", name="Willow"),
    StoryParams(place="porch", problem="silly_shoes", tool="shoe_pairs", name="Willow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/2."))
        pairs = sorted(set(asp.atoms(model, "compatible_story")))
        for pid, tid in pairs:
            print(pid, tid)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.name}: {p.problem} via {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
