#!/usr/bin/env python3
"""
storyworlds/worlds/tweezers_twist_repetition_nursery_rhyme.py
=============================================================

A small story world in a nursery-rhyme style: a child, a tiny snag, a repeated
attempt, and a twist that turns the moment into a tidy ending.

Premise:
- A child loves keeping a small basket of ribbons and beads neat.
- A tiny splinter or bead gets stuck in a toy or mitten.
- The child reaches for tweezers to pull it out.

Twist:
- The first careful try fails because the piece twists deeper or slips away.
- Repetition matters: a second, gentler try with good light and a steady hand
  succeeds.

The world tracks physical meters and emotional memes, and it renders a short,
child-facing tale from state changes rather than from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


@dataclass
class Room:
    place: str
    light: str
    affordances: set[str] = field(default_factory=set)
    sound: str = ""
    mood: str = ""


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    location: str
    twisty: bool = False
    tiny: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    careful: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    problem: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = copy.deepcopy(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _article(phrase: str) -> str:
    return phrase if phrase.startswith(("a ", "an ", "the ")) else f"a {phrase}"


def problem_at_risk(problem: Problem, room: Room) -> bool:
    return problem.location in room.affordances


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for problem_id, problem in PROBLEMS.items():
            if not problem_at_risk(problem, room):
                continue
            for tool_id, tool in TOOLS.items():
                if tool.purpose == problem_id and tool.careful:
                    combos.append((room_id, problem_id, tool_id))
    return combos


def explain_rejection(problem: Problem, room: Room, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} cannot help with {problem.label} in {room.place}. "
        f"Pick a problem that can really be reached there, and a tool that fits it.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme story world about tweezers, twists, and a second try."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        if args.room and args.problem and args.tool:
            raise StoryError(explain_rejection(PROBLEMS[args.problem], ROOMS[args.room], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")
    room, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _choose_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, problem=problem, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def _setup(world: World, child: Entity, parent: Entity, problem: Problem) -> None:
    child.memes["joy"] += 1
    child.memes["care"] += 1
    world.say(
        f"Little {child.id} sat in {world.room.place}, where the {world.room.sound} "
        f"felt soft and the air smelled bright and clean."
    )
    world.say(
        f"{child.id} liked to keep things neat, and {child.pronoun('possessive')} "
        f"{parent.label_word if hasattr(parent, 'label_word') else parent.label} liked that too."
    )
    world.say(
        f"One small morning, {child.id} found {problem.phrase} near {problem.location}."
    )


def _first_try(world: World, child: Entity, problem: Problem, tool: Tool) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} picked up {tool.phrase} and tried to fix it at once."
    )
    if problem.twisty:
        child.memes["frustration"] += 1
        world.say(
            f"But the little bit twisted and twirled, and the first try only made it wiggle deeper."
        )
        world.event("twist", problem=problem.id)
    else:
        world.say(
            f"But the tiny piece slipped, and the first try did not quite do the trick."
        )
        world.event("slip", problem=problem.id)


def _second_try(world: World, child: Entity, problem: Problem, tool: Tool) -> None:
    child.memes["patience"] += 1
    world.say(
        f"{child.id} took a breath, held {tool.label} steady, and tried again and again."
    )
    world.say(
        f"This time the tweezers caught the tiny end, and out it came with a plink."
    )
    world.event("success", problem=problem.id, tool=tool.id)


def _finish(world: World, child: Entity, parent: Entity, problem: Problem) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{child.id} showed {parent.pronoun('object')} the little bit on the cloth, then set the cloth back in its nest."
    )
    world.say(
        f"{parent.id if parent.id else 'Parent'} smiled, and {child.id} smiled too; the room was neat again, and the basket sat straight."
    )


def tell(room: Room, problem: Problem, tool: Tool, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(room)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait], attrs={"room": room.place}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    child.kind = "character"
    child.memes["care"] = 0.0
    parent.memes["care"] = 0.0
    world.facts.update(room=room, problem=problem, tool=tool, child=child, parent=parent, trait=trait)
    _setup(world, child, parent, problem)
    world.para()
    _first_try(world, child, problem, tool)
    world.para()
    _second_try(world, child, problem, tool)
    world.para()
    _finish(world, child, parent, problem)
    world.facts["done"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme style story for a young child about {f["child"].id}, {f["problem"].label}, and {f["tool"].label}. Include the word "tweezers".',
        f"Tell a gentle story where {f['child'].id} tries to solve a tiny twisty problem in {f['room'].place} with {f['tool'].label}, but must try twice before it works.",
        f'Write a cozy story with a repeated attempt and a happy ending in which {f["child"].id} uses tweezers to fix a little snag.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    problem = f["problem"]
    tool = f["tool"]
    room = f["room"]
    return [
        QAItem(
            question=f"What did {child.id} find in {room.place}?",
            answer=f"{child.id} found {problem.phrase} near {problem.location}. It was a tiny thing, but it got in the way and needed careful hands.",
        ),
        QAItem(
            question=f"Why did {child.id} have to try twice with {tool.label}?",
            answer=f"The first try did not work because the little piece twisted and slipped away. After that, {child.id} slowed down and tried again with a steadier hand.",
        ),
        QAItem(
            question=f"How did {child.id} feel when the little piece finally came out?",
            answer=f"{child.id} felt proud and relieved. The tricky bit was gone, and the room was neat again, so {parent.label_word if hasattr(parent, 'label_word') else 'the parent'} could smile too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags) | set(world.facts["tool"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag]
            out.append(QAItem(question=q, answer=a))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} memes={dict((k, v) for k, v in e.memes.items() if v)}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    world = tell(room, problem, tool, params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(R,P,T) :- room(R), problem(P), tool(T), afford(R,P), fits(P,T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for p in sorted(room.affordances):
            lines.append(asp.fact("afford", rid, p))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if problem.twisty:
            lines.append(asp.fact("twisty", pid))
        for tag in sorted(problem.tags):
            lines.append(asp.fact("ptag", pid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.careful:
            lines.append(asp.fact("careful", tid))
        lines.append(asp.fact("fits", tool.purpose, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(valid_combos()) == set(asp_valid_combos())
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    if ok and sample.story:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    print("FAIL: verify checks did not pass.")
    return 1


ROOMS = {
    "nursery": Room(place="the nursery", light="soft morning light", affordances={"nose", "mitten"}, sound="hush of the curtains", mood="cozy"),
    "playroom": Room(place="the playroom", light="bright daylight", affordances={"toy", "ribbon"}, sound="tap of blocks", mood="cheery"),
    "corner": Room(place="the sunny corner", light="golden light", affordances={"sock", "cloth"}, sound="hum of a little lamp", mood="warm"),
}

PROBLEMS = {
    "splinter": Problem(id="splinter", label="a tiny splinter", phrase="a tiny splinter", location="a mitten", twisty=True, tags={"twist", "tiny"}),
    "bead": Problem(id="bead", label="a stuck bead", phrase="a stuck bead", location="a ribbon loop", twisty=True, tags={"repetition", "tiny"}),
    "thread": Problem(id="thread", label="a twisted thread", phrase="a twisted thread", location="a sock seam", twisty=True, tags={"twist", "repetition"}),
}

TOOLS = {
    "tweezers": Tool(id="tweezers", label="tweezers", phrase="the tweezers", purpose="splinter", careful=True, tags={"tweezers"}),
    "small_tweezers": Tool(id="small_tweezers", label="little tweezers", phrase="the little tweezers", purpose="bead", careful=True, tags={"tweezers"}),
    "tiny_tweezers": Tool(id="tiny_tweezers", label="tiny tweezers", phrase="the tiny tweezers", purpose="thread", careful=True, tags={"tweezers"}),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Zoe", "Ada"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Max", "Eli"]
TRAITS = ["patient", "gentle", "careful", "quiet"]


def valid_scenario(room: str, problem: str, tool: str) -> bool:
    return (room, problem, tool) in valid_combos()


CURATED = [
    StoryParams(room="nursery", problem="splinter", tool="tweezers", name="Lily", gender="girl", parent="mother", trait="careful"),
    StoryParams(room="playroom", problem="bead", tool="small_tweezers", name="Tom", gender="boy", parent="father", trait="patient"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.problem and args.tool and not valid_scenario(args.room, args.problem, args.tool):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], ROOMS[args.room], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _choose_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, problem=problem, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


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
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
