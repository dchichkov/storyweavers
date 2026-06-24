#!/usr/bin/env python3
"""
A small storyworld about geese, repetition, friendship, and a rhyme-filled adventure.

This world models a tiny classical tale:
- a flock of geese wants to travel
- one goose is separated by a simple problem
- friends repeat a call-and-response rhyme to find each other
- the group reunites and continues the adventure together
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    path: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"goose", "bird", "friend"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    features: set[str] = field(default_factory=set)
    calls: set[str] = field(default_factory=set)


@dataclass
class Call:
    id: str
    line: str
    reply: str
    mood: str
    effect: str


@dataclass
class Problem:
    id: str
    label: str
    obstacle: str
    turn: str
    risk: str
    solution: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "pond": Place(name="the pond", features={"water", "reeds", "sky"}, calls={"honk"}),
    "marsh": Place(name="the marsh", features={"water", "grass", "mud"}, calls={"honk"}),
    "hill": Place(name="the hill", features={"wind", "grass", "path"}, calls={"honk"}),
    "farm": Place(name="the farm pond", features={"water", "barn", "path"}, calls={"honk"}),
}

CALLS = {
    "honk": Call(
        id="honk",
        line="Honk-honk, come along!",
        reply="Honk-honk, we're on our way!",
        mood="brave",
        effect="the call carried over the water",
    ),
    "echo": Call(
        id="echo",
        line="Honk along the path!",
        reply="Honk along the path!",
        mood="cheerful",
        effect="the rhyme bounced from goose to goose",
    ),
}

PROBLEMS = {
    "fog": Problem(
        id="fog",
        label="fog",
        obstacle="a white fog rolled over the water",
        turn="the flock could not see the far reeds",
        risk="one goose might wander off",
        solution="they kept calling the rhyme until every goose answered",
    ),
    "reeds": Problem(
        id="reeds",
        label="reeds",
        obstacle="tall reeds shook in the wind",
        turn="the smallest goose disappeared behind the green stems",
        risk="the others might leave without it",
        solution="the friends repeated the call and waited for the reply",
    ),
    "current": Problem(
        id="current",
        label="current",
        obstacle="a quick current tugged at the water",
        turn="one goose drifted away from the group",
        risk="the adventure would split apart",
        solution="the flock swam in a line and sang the rhyme together",
    ),
}


@dataclass
class StoryParams:
    place: str
    call: str
    problem: str
    leader_name: str
    friend_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for call_id in place.calls:
            for problem_id in PROBLEMS:
                combos.append((place_id, call_id, problem_id))
    return combos


def explain_rejection(place_id: str, call_id: str, problem_id: str) -> str:
    return (
        f"(No story: the combination {place_id!r}, {call_id!r}, {problem_id!r} "
        f"does not leave room for a clear goose-adventure turn and reunion.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    leader = world.add(Entity(id=params.leader_name, kind="character", type="goose", label="leader goose", plural=False))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="goose", label="friend goose", plural=False))
    flock = world.add(Entity(id="flock", kind="thing", type="flock", label="the flock", plural=True))

    world.facts.update(
        leader=leader,
        friend=friend,
        flock=flock,
        call=CALLS[params.call],
        problem=PROBLEMS[params.problem],
        place=world.place,
    )
    return world


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    leader = world.get(world.facts["leader"].id)
    friend = world.get(world.facts["friend"].id)
    problem = world.facts["problem"]

    if ("problem", problem.id) not in world.fired:
        world.fired.add(("problem", problem.id))
        out.append(problem.obstacle)

    if leader.memes.get("lost", 0) >= 1 and ("call", world.facts["call"].id) not in world.fired:
        world.fired.add(("call", world.facts["call"].id))
        out.append(f'Then {leader.id} called, "{world.facts["call"].line}"')

    if friend.memes.get("heard", 0) >= 1 and ("reply", world.facts["call"].id) not in world.fired:
        world.fired.add(("reply", world.facts["call"].id))
        out.append(f'{friend.id} answered, "{world.facts["call"].reply}"')

    if leader.memes.get("found", 0) >= 1 and friend.memes.get("found", 0) >= 1 and ("reunion", 1) not in world.fired:
        world.fired.add(("reunion", 1))
        out.append("The friends flew and swam back together.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(world: World) -> World:
    leader = world.get(world.facts["leader"].id)
    friend = world.get(world.facts["friend"].id)
    call = world.facts["call"]
    problem = world.facts["problem"]

    world.say(f"At {world.place.name}, {leader.id} and {friend.id} were two young geese who loved an adventure.")
    world.say(f"They liked to travel in a line and to repeat the same small rhyme: \"{call.line}\"")
    world.say(f"When one goose said the first line, the other goose always answered, \"{call.reply}\"")

    world.para()
    world.say(f"One morning, the flock set out across {world.place.name}.")
    world.say(problem.obstacle)
    world.say(f"{problem.turn}.")
    leader.memes["lost"] = 1
    friend.memes["heard"] = 1
    propagate(world)

    world.para()
    world.say(f"{leader.id} did not stop calling.")
    world.say(f"{problem.solution}.")
    leader.memes["found"] = 1
    friend.memes["found"] = 1
    propagate(world)

    world.para()
    world.say(f"At last, the geese crossed {world.place.name} side by side.")
    world.say(f"The little rhyme still rang out, and the brave friends stayed together for the rest of the trip.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_name(P).
call(C) :- call_name(C).
problem(X) :- problem_name(X).

valid_story(P, C, X) :- place(P), call(C), problem(X), place_calls(P, C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        for c in sorted(place.calls):
            lines.append(asp.fact("place_calls", pid, c))
    for cid in CALLS:
        lines.append(asp.fact("call_name", cid))
    for x in PROBLEMS:
        lines.append(asp.fact("problem_name", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Prompts / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about geese that includes the repeated line "{f["call"].line}".',
        f"Tell a gentle story where {f['leader'].id} and {f['friend'].id} get separated at {world.place.name} and find each other by calling back and forth.",
        f"Write a rhyme-filled goose adventure with friendship, repetition, and a happy ending at {world.place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    leader = f["leader"].id
    friend = f["friend"].id
    place = world.place.name
    call = f["call"]
    problem = f["problem"]

    return [
        QAItem(
            question=f"Who were the two geese in the story at {place}?",
            answer=f"The story was about {leader} and {friend}, two friendly geese who went on an adventure together.",
        ),
        QAItem(
            question=f"What rhyme did the geese repeat while they traveled through {place}?",
            answer=f'They repeated "{call.line}" and answered with "{call.reply}".',
        ),
        QAItem(
            question=f"What problem made the adventure tricky at {place}?",
            answer=f"{problem.obstacle.capitalize()}. That made the flock worry that one goose might get left behind.",
        ),
        QAItem(
            question=f"How did the geese solve the problem at {place}?",
            answer=f"They kept repeating the rhyme and waited for each reply until the friends found each other again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "honk": [
        QAItem(
            question="Why do geese honk?",
            answer="Geese honk to call to one another and help the flock stay together.",
        )
    ],
    "water": [
        QAItem(
            question="Why do geese like water?",
            answer="Geese like water because they can swim on it and move around safely together.",
        )
    ],
    "repetition": [
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when the same words or sounds are used again and again so they are easy to remember.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is caring about someone, helping them, and staying close when things are hard.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a playful pattern of words or sounds that end in a similar sound, like a little song.",
        )
    ],
    "adventure": [
        QAItem(
            question="What makes a story an adventure?",
            answer="An adventure story usually has a trip, a problem to solve, and a brave ending.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["honk"])
    out.extend(WORLD_KNOWLEDGE["water"])
    out.extend(WORLD_KNOWLEDGE["repetition"])
    out.extend(WORLD_KNOWLEDGE["friendship"])
    out.extend(WORLD_KNOWLEDGE["rhyme"])
    out.extend(WORLD_KNOWLEDGE["adventure"])
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
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.path:
            bits.append(f"path={e.path}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="pond", call="honk", problem="fog", leader_name="Gus", friend_name="Mabel"),
    StoryParams(place="marsh", call="echo", problem="reeds", leader_name="Nell", friend_name="Otis"),
    StoryParams(place="hill", call="honk", problem="current", leader_name="Pip", friend_name="June"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Geese adventure storyworld with repetition, friendship, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--call", choices=CALLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--leader-name")
    ap.add_argument("--friend-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.call is None or c[1] == args.call)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, call, problem = rng.choice(sorted(combos))
    leader = args.leader_name or rng.choice(["Gus", "Nell", "Pip", "Mabel", "Otis", "June"])
    friend = args.friend_name or rng.choice([n for n in ["Gus", "Nell", "Pip", "Mabel", "Otis", "June"] if n != leader])
    return StoryParams(place=place, call=call, problem=problem, leader_name=leader, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, call, problem) combos:\n")
        for place, call, problem in combos:
            print(f"  {place:8} {call:6} {problem}")
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
            header = f"### {p.leader_name} and {p.friend_name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
