#!/usr/bin/env python3
"""
storyworlds/worlds/node_sloth_tournament_mystery_to_solve_space.py
===================================================================

A small space-adventure storyworld about a sloth, a tournament, and a mystery
to solve at a node in a star network.

Premise:
- A slow but clever sloth wants to compete in a space tournament.
- The tournament is interrupted by a mystery: a missing beacon key at a node.
- The hero cannot win until the mystery is solved and the route is restored.

World model:
- Physical meters model distance, signal strength, battery charge, and object state.
- Emotional memes model worry, courage, pride, curiosity, and relief.
- The story is generated from state changes rather than a frozen template.

This world is designed to read like a child-friendly space adventure with a
clear beginning, turn, and ending image.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    at: str = ""
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sloth"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    kind: str
    signal: int
    clues: tuple[str, ...]


@dataclass(frozen=True)
class Route:
    from_node: str
    to_node: str
    open: bool = True


@dataclass(frozen=True)
class Tournament:
    name: str
    event: str
    prize: str
    stage: str


@dataclass
class StoryParams:
    node: str
    sloth_name: str
    tournament: str
    seed: Optional[int] = None


class World:
    def __init__(self, node: Node, tournament: Tournament) -> None:
        self.node = node
        self.tournament = tournament
        self.entities: dict[str, Entity] = {}
        self.routes: dict[tuple[str, str], Route] = {}
        self.fired: set[str] = set()
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
        clone = World(self.node, self.tournament)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.routes = copy.deepcopy(self.routes)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def route_open(self, a: str, b: str) -> bool:
        r = self.routes.get((a, b)) or self.routes.get((b, a))
        return bool(r and r.open)


SPACE_NODES = {
    "node_alpha": Node(
        id="node_alpha",
        label="Alpha Node",
        kind="relay",
        signal=3,
        clues=("glimmer", "ring", "echo"),
    ),
    "node_comet": Node(
        id="node_comet",
        label="Comet Node",
        kind="relay",
        signal=2,
        clues=("spark", "trail", "whisper"),
    ),
    "node_luna": Node(
        id="node_luna",
        label="Luna Node",
        kind="relay",
        signal=1,
        clues=("silver", "dust", "footprint"),
    ),
}

TOURNAMENTS = {
    "starcup": Tournament(
        name="Star Cup",
        event="signal puzzle",
        prize="a bright ribbon badge",
        stage="the gravity-ring stage",
    ),
    "orbit_open": Tournament(
        name="Orbit Open",
        event="navigation race",
        prize="a comet medal",
        stage="the loop gate",
    ),
    "meteor_match": Tournament(
        name="Meteor Match",
        event="code riddle",
        prize="a shining moon pin",
        stage="the lantern deck",
    ),
}


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    detail: str


GEAR = {
    "toolkit": Gear("toolkit", "a little toolkit", "a tiny wrench and a beam-lamp"),
    "scanner": Gear("scanner", "a pocket scanner", "a blinking glass scanner"),
    "gloves": Gear("gloves", "soft space gloves", "soft gloves with silver dots"),
}


@dataclass
class Mystery:
    missing: str
    hidden_by: str
    solved_by: str


MYSTERY = Mystery(
    missing="beacon key",
    hidden_by="a dust curl behind the node panel",
    solved_by="careful scanning",
)


def build_routes() -> dict[tuple[str, str], Route]:
    return {
        ("node_alpha", "node_comet"): Route("node_alpha", "node_comet", True),
        ("node_comet", "node_luna"): Route("node_comet", "node_luna", True),
        ("node_alpha", "node_luna"): Route("node_alpha", "node_luna", False),
    }


def node_intro(node: Node) -> str:
    return {
        "relay": f"{node.label} blinked like a tiny star at the center of the route map.",
    }.get(node.kind, f"{node.label} floated in the quiet dark.")


def clue_sentence(node: Node) -> str:
    clues = ", ".join(node.clues[:-1]) + f", and {node.clues[-1]}"
    return f"The panels left little clues: {clues}."


def predict_route(world: World) -> bool:
    return world.route_open(world.node.id, "node_comet")


def solve_mystery(world: World, sloth: Entity, use: Gear) -> bool:
    if use.id != "scanner":
        return False
    sloth.memes["curiosity"] = sloth.memes.get("curiosity", 0) + 1
    world.say(
        f"{sloth.id} held up {use.label} and listened to its soft beep-beep."
    )
    world.say(
        f"The beam found {MYSTERY.hidden_by}, and there was the missing {MYSTERY.missing}."
    )
    world.facts["mystery_solved"] = True
    return True


def start_tournament(world: World, sloth: Entity) -> None:
    sloth.memes["worry"] = sloth.memes.get("worry", 0) + 1
    world.say(
        f"{sloth.id} had come for {world.tournament.name}, where the event was a {world.tournament.event}."
    )
    world.say(
        f"{sloth.id} wanted to win {world.tournament.prize} at {world.tournament.stage}, but the route had gone dim."
    )


def find_problem(world: World, sloth: Entity) -> None:
    world.say(
        f"At {world.node.label}, the route to the next gate was stuck because someone had lost the {MYSTERY.missing}."
    )
    world.say(clue_sentence(world.node))


def ask_for_help(world: World, sloth: Entity) -> Gear:
    gear = GEAR["scanner"]
    world.say(
        f"A friendly dock helper passed {sloth.id} {gear.label} and whispered that it could help solve the puzzle."
    )
    return gear


def finish_world(world: World, sloth: Entity) -> None:
    sloth.memes["worry"] = max(0, sloth.memes.get("worry", 0) - 1)
    sloth.memes["pride"] = sloth.memes.get("pride", 0) + 1
    sloth.memes["relief"] = sloth.memes.get("relief", 0) + 1
    world.say(
        f"With the {MYSTERY.missing} found, the route opened again, and the tournament lights turned gold."
    )
    world.say(
        f"{sloth.id} rolled into the next round just in time, calm and smiling, while {world.node.label} glowed behind {sloth.pronoun('object')}."
    )


def tell(node: Node, tournament: Tournament, sloth_name: str) -> World:
    world = World(node, tournament)
    world.routes = build_routes()

    sloth = world.add(Entity(id=sloth_name, kind="character", type="sloth"))
    helper = world.add(Entity(id="helper", kind="character", type="helper", label="dock helper"))
    beacon = world.add(Entity(id="beacon", kind="thing", type="key", label="beacon key"))
    beacon.at = "hidden"
    world.facts["helper"] = helper
    world.facts["beacon"] = beacon

    start_tournament(world, sloth)
    world.para()
    world.say(node_intro(node))
    find_problem(world, sloth)
    world.say(
        f"{sloth.id} felt slow, but slow did not mean stuck."
    )
    world.say(
        f"{sloth.id} knew a mystery at a node could be solved one careful step at a time."
    )

    world.para()
    gear = ask_for_help(world, sloth)
    solved = solve_mystery(world, sloth, gear)
    if solved:
        world.say(
            f"The helper grinned, because the answer had been there all along in the dust and the blinking light."
        )
    if predict_route(world):
        finish_world(world, sloth)
    else:
        raise StoryError("The route should be open for the chosen node, but it is not.")

    world.facts.update(
        sloth=sloth,
        gear=gear,
        solved=solved,
        route_open=True,
        node=node,
        tournament=tournament,
    )
    return world


def valid_nodes() -> list[str]:
    return list(SPACE_NODES.keys())


def valid_tournaments() -> list[str]:
    return list(TOURNAMENTS.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space adventure storyworld: a sloth solves a mystery at a node during a tournament."
    )
    ap.add_argument("--node", choices=valid_nodes())
    ap.add_argument("--tournament", choices=valid_tournaments())
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
    node = args.node or rng.choice(valid_nodes())
    tournament = args.tournament or rng.choice(valid_tournaments())
    name = args.name or rng.choice(["Milo", "Pip", "Nova", "Tali", "Bean"])
    return StoryParams(node=node, sloth_name=name, tournament=tournament)


def generate(params: StoryParams) -> StorySample:
    world = tell(SPACE_NODES[params.node], TOURNAMENTS[params.tournament], params.sloth_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short space adventure about a sloth who solves a mystery at a node during a tournament.",
        f"Tell a child-friendly story where {world.facts['sloth'].id} uses a small tool to find a missing beacon key.",
        f"Write a simple space story about {world.node.label}, a tournament, and a mystery that turns out to be easy to solve with help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    sloth: Entity = world.facts["sloth"]
    node = world.node
    tournament = world.tournament
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {sloth.id}, a slow but clever sloth at {node.label} during {tournament.name}.",
        ),
        QAItem(
            question=f"What mystery had to be solved?",
            answer=f"The missing {MYSTERY.missing} had to be found so the route could open again.",
        ),
        QAItem(
            question=f"How did {sloth.id} solve the problem?",
            answer=f"{sloth.id} used {world.facts['gear'].label} and careful scanning to find the hidden key.",
        ),
        QAItem(
            question=f"What happened after the mystery was solved?",
            answer=f"The route opened, the tournament lights turned gold, and {sloth.id} moved on to the next round smiling.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    node = world.node
    tournament = world.tournament
    return [
        QAItem(
            question="What is a node in a space story?",
            answer="A node is a stopping place where routes can meet, blink, and carry signals to other places.",
        ),
        QAItem(
            question="What is a tournament?",
            answer="A tournament is a contest where someone takes part in a game, puzzle, or race to try to win a prize.",
        ),
        QAItem(
            question="What does a sloth usually do?",
            answer="A sloth usually moves slowly, hangs on with strong limbs, and takes careful, gentle steps.",
        ),
        QAItem(
            question=f"Why was {node.label} important?",
            answer=f"{node.label} mattered because its route lights and clues helped the tournament continue.",
        ),
        QAItem(
            question=f"What kind of event was {tournament.name}?",
            answer=f"{tournament.name} was a space tournament with {tournament.event} and a prize for the winner.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.at:
            bits.append(f"at={e.at}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  node: {world.node.id}")
    lines.append(f"  tournament: {world.tournament.name}")
    lines.append(f"  route open: {world.facts.get('route_open')}")
    lines.append(f"  mystery solved: {world.facts.get('mystery_solved')}")
    return "\n".join(lines)


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


ASP_RULES = r"""
node(N) :- node_fact(N).
tournament(T) :- tournament_fact(T).
mystery(M) :- mystery_fact(M).

compatible(N, T) :- node(N), tournament(T), route_open(N).
solves(M) :- mystery(M), clue_present(M), helper_available.
valid_story(N, T, M) :- compatible(N, T), solves(M).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("node_fact", nid) for nid in SPACE_NODES]
    lines += [asp.fact("tournament_fact", tid) for tid in TOURNAMENTS]
    lines.append(asp.fact("mystery_fact", MYSTERY.missing.replace(" ", "_")))
    lines.append(asp.fact("route_open", "node_alpha"))
    lines.append(asp.fact("route_open", "node_comet"))
    lines.append(asp.fact("clue_present", MYSTERY.missing.replace(" ", "_")))
    lines.append(asp.fact("helper_available"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (n, t, MYSTERY.missing.replace(" ", "_"))
        for n in SPACE_NODES
        for t in TOURNAMENTS
        if n in {"node_alpha", "node_comet"}
    }
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(cl)} stories).")
        return 0
    print("MISMATCH between ASP and python gates:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(node="node_alpha", sloth_name="Milo", tournament="starcup"),
    StoryParams(node="node_comet", sloth_name="Nova", tournament="orbit_open"),
    StoryParams(node="node_alpha", sloth_name="Bean", tournament="meteor_match"),
]


def explain_rejection(node: str, tournament: str) -> str:
    return f"(No story: {node} does not fit {tournament} in this tiny space adventure.)"


def valid_combos() -> list[tuple[str, str]]:
    return [("node_alpha", t) for t in TOURNAMENTS] + [("node_comet", t) for t in TOURNAMENTS]


def resolve_specific(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        triples = asp_valid()
        print(f"{len(triples)} valid story triples:\n")
        for item in triples:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_specific(args, random.Random(seed))
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
            header = f"### {p.sloth_name}: {p.node} / {p.tournament}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
