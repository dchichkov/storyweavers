#!/usr/bin/env python3
"""
storyworlds/worlds/graph_sound_effects_transformation_quest_adventure.py
=======================================================================

A small adventure storyworld about a child following a graph-map,
listening for sound effects, and completing a quest that causes a
gentle transformation.

Premise:
- A child receives a hand-drawn graph map with landmarks as nodes and paths as edges.
- Along the way, the child hears sound effects that help identify the right route.
- The quest is to reach a hidden place and transform something ordinary into something useful.
- The story turns when the map's graph logic reveals the correct path, and the ending proves
  the transformation happened.

This world is intentionally small and constraint-checked: the route must be connected, the
quest must be reachable, and the transformation must make sense for the object's current form.
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
class Node:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Edge:
    a: str
    b: str
    sound: str
    difficult: bool = False


@dataclass
class QuestItem:
    id: str
    label: str
    form: str
    transformed_form: str
    transform_sound: str
    holds: set[str] = field(default_factory=set)  # forms it can hold or become


@dataclass
class StoryParams:
    start: str
    goal: str
    item: str
    hero_name: str
    hero_kind: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.hero: Optional[Node] = None
        self.sidekick: Optional[Node] = None
        self.item: Optional[QuestItem] = None
        self.start: str = ""
        self.goal: str = ""
        self.path: list[str] = []
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def node(self, nid: str) -> Node:
        return self.nodes[nid]

    def neighbors(self, nid: str) -> list[tuple[str, Edge]]:
        out = []
        for e in self.edges:
            if e.a == nid:
                out.append((e.b, e))
            elif e.b == nid:
                out.append((e.a, e))
        return out


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NODES = {
    "camp": ("camp", "camp", "safe"),
    "bridge": ("bridge", "wobbly bridge", "middle"),
    "hill": ("hill", "little hill", "high"),
    "cave": ("cave", "echo cave", "dark"),
    "lake": ("lake", "quiet lake", "water"),
    "tower": ("tower", "windy tower", "high"),
    "garden": ("garden", "glow garden", "bright"),
}

EDGES = [
    Edge("camp", "bridge", "creak-creak", difficult=True),
    Edge("bridge", "hill", "thump-thump"),
    Edge("hill", "cave", "drip-drop"),
    Edge("bridge", "lake", "splish-splash"),
    Edge("lake", "garden", "shhh-rrr"),
    Edge("hill", "tower", "whoooosh", difficult=True),
    Edge("cave", "garden", "plink-plink"),
]

ITEMS = {
    "lantern": QuestItem(
        id="lantern",
        label="lantern",
        form="dim lantern",
        transformed_form="bright lantern",
        transform_sound="fzzzt",
        holds={"dim lantern", "bright lantern"},
    ),
    "key": QuestItem(
        id="key",
        label="key",
        form="plain key",
        transformed_form="shining key",
        transform_sound="ting!",
        holds={"plain key", "shining key"},
    ),
    "shell": QuestItem(
        id="shell",
        label="shell",
        form="quiet shell",
        transformed_form="singing shell",
        transform_sound="hummm",
        holds={"quiet shell", "singing shell"},
    ),
}

HERO_NAMES = ["Milo", "Nia", "Zuri", "Arlo", "Pia", "Tess", "Juno", "Finn"]
SIDEKICKS = ["a chatty robin", "a brave squirrel", "a tiny robot", "a clever moth"]
HERO_KINDS = ["boy", "girl", "child"]
TRANSFORMATIONS = {
    "lantern": "bright lantern",
    "key": "shining key",
    "shell": "singing shell",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A path exists when edges connect nodes.
reach(X,X).
reach(X,Y) :- edge(X,Y,_).
reach(X,Y) :- edge(X,Z,_), reach(Z,Y).

% The quest is valid if the goal is reachable from the start.
valid_quest(S,G,I) :- start(S), goal(G), item(I), reach(S,G).

% A transformation is valid if it changes form in a meaningful way.
valid_transform(I) :- item(I), item_form(I,F1), transformed_form(I,F2), F1 != F2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for nid, (kind, label, _) in NODES.items():
        lines.append(asp.fact("node", nid))
        lines.append(asp.fact("node_kind", nid, kind))
        lines.append(asp.fact("node_label", nid, label))
    for e in EDGES:
        lines.append(asp.fact("edge", e.a, e.b, e.sound))
        lines.append(asp.fact("edge", e.b, e.a, e.sound))
        if e.difficult:
            lines.append(asp.fact("difficult", e.a, e.b))
            lines.append(asp.fact("difficult", e.b, e.a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_form", iid, item.form))
        lines.append(asp.fact("transformed_form", iid, item.transformed_form))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\nstart(camp).\ngoal(garden).\nitem(lantern).\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_quest/3.\n#show valid_transform/1."))
    got_q = set(asp.atoms(model, "valid_quest"))
    got_t = set(asp.atoms(model, "valid_transform"))
    want_q = {(params.start, params.goal, params.item) for params in [StoryParams("camp", "garden", "lantern", "Milo", "child", "a chatty robin")]}
    want_t = {("lantern",)}
    if got_q and got_t:
        print("OK: ASP model produced a reachable quest and a valid transformation.")
        return 0
    print("ASP verification failed.")
    return 1


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with graph paths, sound cues, and transformation quests.")
    ap.add_argument("--start", choices=NODES)
    ap.add_argument("--goal", choices=[n for n in NODES if n != "camp"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--kind", choices=HERO_KINDS)
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
    start = args.start or "camp"
    goal = args.goal or rng.choice(["garden", "tower", "cave", "lake"])
    item = args.item or rng.choice(list(ITEMS))
    if start == goal:
        raise StoryError("start and goal must be different.")
    name = args.name or rng.choice(HERO_NAMES)
    kind = args.kind or rng.choice(HERO_KINDS)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    if not route_exists(start, goal):
        raise StoryError("No connected route exists from the chosen start to the chosen goal.")
    return StoryParams(start=start, goal=goal, item=item, hero_name=name, hero_kind=kind, sidekick=sidekick)


def route_exists(start: str, goal: str) -> bool:
    seen = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur == goal:
            return True
        for nxt, _ in WorldNeighbors(cur):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def WorldNeighbors(nid: str) -> list[tuple[str, Edge]]:
    w = World()
    w.edges = EDGES
    return w.neighbors(nid)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World()
    for nid, (kind, label, _) in NODES.items():
        world.add_node(Node(id=nid, label=label, kind=kind))
    world.edges = list(EDGES)
    world.hero = world.add_node(Node(id="hero", label=params.hero_name, kind=params.hero_kind, meters={"hope": 1.0}, memes={"curiosity": 1.0}))
    world.sidekick = world.add_node(Node(id="sidekick", label=params.sidekick, kind="helper"))
    world.item = ITEMS[params.item]
    world.start = params.start
    world.goal = params.goal
    world.path = shortest_path(params.start, params.goal)
    if not world.path:
        raise StoryError("Could not find a path for the quest.")
    if params.item == "lantern" and params.goal not in {"cave", "tower", "garden"}:
        raise StoryError("The lantern quest needs a place where light matters.")
    if params.item == "key" and params.goal not in {"cave", "tower", "garden"}:
        raise StoryError("The key quest needs a place with a gate, box, or lock-like ending.")
    if params.item == "shell" and params.goal not in {"lake", "garden", "cave"}:
        raise StoryError("The shell quest needs a place where sound can answer back.")
    return world


def shortest_path(start: str, goal: str) -> list[str]:
    from collections import deque
    q = deque([(start, [start])])
    seen = {start}
    while q:
        cur, path = q.popleft()
        if cur == goal:
            return path
        for nxt, _ in WorldNeighbors(cur):
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, path + [nxt]))
    return []


def narrate(world: World) -> None:
    hero = world.hero
    sidekick = world.sidekick
    item = world.item
    assert hero and sidekick and item
    start_label = world.node(world.start).label
    goal_label = world.node(world.goal).label

    world.say(
        f"{hero.label} found a hand-drawn graph map at {start_label}. "
        f"{sidekick.label} pointed at the dots and said the lines could lead to a quest."
    )
    world.say(
        f"In {hero.label}'s bag was a {item.form}. The map said it could become a {item.transformed_form} if the right sound was found."
    )

    world.para()
    path = world.path
    for i in range(len(path) - 1):
        cur, nxt = path[i], path[i + 1]
        edge = next(e for e in EDGES if {e.a, e.b} == {cur, nxt})
        cur_label = world.node(cur).label
        nxt_label = world.node(nxt).label
        world.say(
            f"They went from {cur_label} to {nxt_label}, listening for {edge.sound}. "
            f"The sound matched the line on the graph, so they knew the route was right."
        )
        if edge.difficult:
            world.say(
                f"The path was tricky there, but {hero.label} kept going because the quest was bigger than the wobble."
            )

    world.para()
    end_sound = transform_sound(item.id)
    world.say(
        f"At {goal_label}, the last clue rang out: {end_sound}. "
        f"{hero.label} held the {item.form} still, and it changed into a {item.transformed_form}."
    )
    world.say(
        f"That new {item.transformed_form} lit the way at {goal_label}, and {hero.label} smiled at the neat graph that had led them there."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        item=item,
        start=world.start,
        goal=world.goal,
        path=path,
        goal_label=goal_label,
    )


def transform_sound(item_id: str) -> str:
    return ITEMS[item_id].transform_sound


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about a graph map, a sound cue, and a quest to transform a {f["item"].label}.',
        f"Tell a child-friendly adventure where {f['hero'].label} follows a graph from {world.node(f['start']).label} to {world.node(f['goal']).label} with help from {f['sidekick'].label}.",
        f'Write a small adventure with the word "graph" in it, where a sound effect helps a hero finish a quest and change an object.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    path = f["path"]
    start_label = world.node(f["start"]).label
    goal_label = f["goal_label"]

    return [
        QAItem(
            question=f"What kind of map helped {hero.label} on the quest?",
            answer=f"A graph map helped {hero.label}. It used dots and lines to show the route from {start_label} to {goal_label}.",
        ),
        QAItem(
            question=f"What sound did they listen for on the way?",
            answer=f"They listened for sounds like {next(e.sound for e in EDGES if {e.a, e.b} == {path[0], path[1]})} and other clue sounds on the path.",
        ),
        QAItem(
            question=f"What did {item.label} become at the end?",
            answer=f"The {item.form} became a {item.transformed_form} at the end of the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a graph?",
            answer="A graph is a set of dots, called nodes, connected by lines, called edges.",
        ),
        QAItem(
            question="Why can sound effects help in a story?",
            answer="Sound effects can act like clues, so a character can notice where to go or what is changing.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal-filled journey where someone tries to reach a place, find something, or solve a problem.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"start={world.start} goal={world.goal} path={world.path}")
    for node in world.nodes.values():
        bits = []
        if node.meters:
            bits.append(f"meters={node.meters}")
        if node.memes:
            bits.append(f"memes={node.memes}")
        lines.append(f"  {node.id:8} ({node.kind:8}) {node.label} {' '.join(bits)}")
    for e in world.edges:
        lines.append(f"  edge {e.a} <-> {e.b} sound={e.sound} difficult={e.difficult}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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
# ASP / CLI
# ---------------------------------------------------------------------------
def valid_triplets() -> list[tuple[str, str, str]]:
    out = []
    for start in ["camp"]:
        for goal in ["garden", "tower", "cave", "lake"]:
            if route_exists(start, goal):
                for item in ITEMS:
                    out.append((start, goal, item))
    return out


def asp_valid_triplets() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_quest/3.\n#show valid_transform/1."))
    return sorted(set(asp.atoms(model, "valid_quest")))


def build_all_params(rng: random.Random) -> list[StoryParams]:
    items = []
    for start, goal, item in valid_triplets():
        items.append(StoryParams(start=start, goal=goal, item=item, hero_name=rng.choice(HERO_NAMES), hero_kind=rng.choice(HERO_KINDS), sidekick=rng.choice(SIDEKICKS)))
    return items


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_quest/3.\n#show valid_transform/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_quest/3.\n#show valid_transform/1."))
        print("valid quest / transform atoms:")
        for atom in asp.atoms(model, "valid_quest"):
            print(" ", atom)
        for atom in asp.atoms(model, "valid_transform"):
            print(" ", atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        params_list = build_all_params(rng)
        for p in params_list:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            sample = generate(p)
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
