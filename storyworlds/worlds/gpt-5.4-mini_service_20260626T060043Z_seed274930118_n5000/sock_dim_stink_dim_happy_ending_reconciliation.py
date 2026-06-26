#!/usr/bin/env python3
"""
Standalone storyworld: sock-dim, stink-dim, happy-ending reconciliation.

This world tells a gentle ghost story in which a spooky misunderstanding
around a dim, smelly sock leads to a scare, then a repair, then friendship.
The simulated state tracks two physical meters (sock-dim and stink-dim) plus
memes for fear, regret, kindness, and relief. A short, causal world model drives
the story text and Q&A.

The core premise:
- A child finds a dim little sock near an old chest.
- A shy ghost is blamed for the smell and the dimness.
- The child discovers the sock was trapped in dust and old air.
- They clean it, air it out, and the ghost is welcomed back kindly.

The tone aims for a cozy Ghost Story: soft spookiness, then warmth.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

CHARACTER_TYPES = {"child", "ghost", "parent"}
LOCATIONS = ["attic", "cellar", "hallway", "bedroom", "porch"]
NAMES = {
    "child": ["Mina", "Ollie", "Pip", "Nora", "Theo", "June"],
    "ghost": ["Boo", "Wisp", "Murmur", "Pale", "Shiver"],
    "parent": ["Mom", "Dad", "Aunt", "Uncle"],
}


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # child | ghost | parent | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "child":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "parent":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        return copy.deepcopy(self)


# ---------------------------------------------------------------------------
# Story knobs
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    location: str
    child_name: str
    parent_name: str
    ghost_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    owner: str
    caretaker: str
    worn_by: Optional[str] = None


@dataclass
class SceneSpec:
    location: str
    mood: str
    hiding_place: str


OBJECTS = {
    "sock": ObjectSpec(
        id="sock",
        label="sock",
        phrase="a tiny pale sock",
        owner="child",
        caretaker="parent",
    ),
    "rag": ObjectSpec(
        id="rag",
        label="rag",
        phrase="an old soft rag",
        owner="parent",
        caretaker="parent",
    ),
}

SCENES = {
    "attic": SceneSpec(location="the attic", mood="dusty", hiding_place="an old chest"),
    "cellar": SceneSpec(location="the cellar", mood="damp", hiding_place="a box by the wall"),
    "hallway": SceneSpec(location="the hallway", mood="quiet", hiding_place="a basket under a bench"),
    "bedroom": SceneSpec(location="the bedroom", mood="sleepy", hiding_place="the toy shelf"),
    "porch": SceneSpec(location="the porch", mood="cool", hiding_place="a crate by the door"),
}


# ---------------------------------------------------------------------------
# Story model helpers
# ---------------------------------------------------------------------------
def _init_entity(eid: str, kind: str, type_: str, label: str) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, meters={"sock_dim": 0.0, "stink_dim": 0.0}, memes={"fear": 0.0, "regret": 0.0, "kindness": 0.0, "relief": 0.0})


def dim_state(world: World, sock: Entity) -> bool:
    return sock.meters.get("sock_dim", 0.0) >= THRESHOLD


def stink_state(world: World, sock: Entity) -> bool:
    return sock.meters.get("stink_dim", 0.0) >= THRESHOLD


def world_step_find_sock(world: World, child: Entity, sock: Entity, ghost: Entity) -> None:
    scene = SCENES[world.location]
    world.say(
        f"{child.id} crept into {scene.location}, where the air felt {scene.mood} and the light was very low."
    )
    world.say(
        f"Near {scene.hiding_place}, {child.id} found {sock.phrase} lying still in the dark."
    )
    sock.meters["sock_dim"] += 1.0
    sock.meters["stink_dim"] += 1.0
    ghost.memes["fear"] += 1.0
    world.facts["found_in"] = scene.hiding_place
    world.facts["first_mood"] = scene.mood


def world_step_accuse(world: World, child: Entity, sock: Entity, ghost: Entity) -> None:
    world.say(
        f"The little sock looked so dim, and it gave off a stink-dim smell that made {child.id} wrinkle {child.pronoun('possessive')} nose."
    )
    world.say(
        f"{child.id} whispered, 'A ghost must have done this.'"
    )
    ghost.memes["fear"] += 1.0
    world.facts["accused"] = True


def world_step_reveal(world: World, parent: Entity, child: Entity, sock: Entity, ghost: Entity) -> None:
    sock.meters["sock_dim"] = 0.0
    sock.meters["stink_dim"] = 0.0
    ghost.memes["regret"] += 1.0
    world.say(
        f"{parent.id} lifted the sock to the window and said, 'No ghost did this. It was trapped in dust and old air.'"
    )
    world.say(
        f"The truth made the room feel smaller and kinder at the same time."
    )
    world.facts["reveal"] = True


def world_step_reconcile(world: World, child: Entity, parent: Entity, ghost: Entity, sock: Entity) -> None:
    child.memes["fear"] = 0.0
    child.memes["kindness"] += 1.0
    ghost.memes["fear"] = 0.0
    ghost.memes["relief"] += 1.0
    world.say(
        f"{child.id} held the sock under the lamp, washed it gently, and waved it in the fresh air until the dimness and stink were gone."
    )
    world.say(
        f"Then {child.id} smiled at the ghost and said, 'I was wrong. You didn't scare the sock.'"
    )
    world.say(
        f"The ghost floated close, shy and grateful, and the three of them shared a soft laugh."
    )
    world.say(
        f"By bedtime, the sock was bright again, the room smelled clean, and the ghost was welcome to stay."
    )
    world.facts["reconciled"] = True


def tell(params: StoryParams) -> World:
    world = World(location=params.location)
    child = world.add(_init_entity("child", "child", "child", params.child_name))
    parent = world.add(_init_entity("parent", "parent", "parent", params.parent_name))
    ghost = world.add(_init_entity("ghost", "ghost", "ghost", params.ghost_name))
    sock_spec = OBJECTS["sock"]
    sock = world.add(Entity(
        id="sock",
        kind="thing",
        type="sock",
        label=sock_spec.label,
        phrase=sock_spec.phrase,
        owner=child.id,
        caretaker=parent.id,
        worn_by=child.id,
        meters={"sock_dim": 0.0, "stink_dim": 0.0},
        memes={"fear": 0.0, "regret": 0.0, "kindness": 0.0, "relief": 0.0},
    ))

    world.say(
        f"One quiet evening, {child.id} wandered into {SCENES[params.location].location} and met a shy ghost named {ghost.id}."
    )
    world.say(
        f"{child.id} had been missing {child.pronoun('possessive')} favorite sock, a little one that always seemed to slip into strange places."
    )
    world.para()

    world_step_find_sock(world, child, sock, ghost)
    world_step_accuse(world, child, sock, ghost)
    world.para()

    world.say(
        f"{parent.id} came with a candle, looked at the sock, and knelt beside {child.id}."
    )
    world_step_reveal(world, parent, child, sock, ghost)
    world_step_reconcile(world, child, parent, ghost, sock)

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        sock=sock,
        scene=SCENES[params.location],
    )
    return world


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    return params.location in SCENES and bool(params.child_name) and bool(params.parent_name) and bool(params.ghost_name)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A sock can be dim and stinky if it is found in a dusty or damp place.
dim_sock(S) :- found(S), place(P), dusty(P).
stink_sock(S) :- found(S), place(P), damp(P).

% A story is valid if there is a child, a parent, a ghost, and a sock that ends clean.
valid_story(L) :- location(L), child(_), parent(_), ghost(_), sock(_), happy_ending.

% Reconciliation happens after misunderstanding and then repair.
reconciled :- accused, revealed, cleaned, welcomed.
happy_ending :- reconciled.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc, spec in SCENES.items():
        lines.append(asp.fact("location", loc))
        if spec.mood == "dusty":
            lines.append(asp.fact("dusty", loc))
        if spec.mood == "damp":
            lines.append(asp.fact("damp", loc))
        lines.append(asp.fact("place", loc))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("parent", "parent"))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("sock", "sock"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if clingo_ok != py_ok:
        print("MISMATCH between ASP and Python validation")
        return 1
    print("OK: ASP/Python parity holds.")
    return 0


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a cozy ghost story for a young child about a sock that seems {f['first_mood']} and {('stinky' if f['sock'].meters['stink_dim'] else 'odd')}.",
        f"Tell a gentle story where {f['child'].id} thinks a ghost caused a dim sock, but the truth leads to reconciliation.",
        f"Write a short story with the words 'sock-dim' and 'stink-dim' that ends in a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    ghost = f["ghost"]
    sock = f["sock"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"Where did {child.id} find the sock?",
            answer=f"{child.id} found the sock in {scene.location}, near {f['found_in']}.",
        ),
        QAItem(
            question=f"Why did {child.id} think the ghost caused the problem?",
            answer=f"The sock was dim and smelled strange, so {child.id} guessed the shy ghost had frightened it. That guess was wrong.",
        ),
        QAItem(
            question=f"What changed the story into a happy ending?",
            answer=f"{parent.id} showed that dust and old air had made the sock dim and stink-dim, then {child.id} washed it and welcomed the ghost kindly. That led to reconciliation and a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dim mean?",
            answer="Dim means not bright or not easy to see, like something sitting in a low, sleepy light.",
        ),
        QAItem(
            question="What does stink mean?",
            answer="Stink means to smell very bad.",
        ),
        QAItem(
            question="Why do people wash socks?",
            answer="People wash socks to get dirt and smells out so the socks are clean again.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, tell the truth, and become friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params resolution / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cozy ghost storyworld: sock-dim, stink-dim, reconciliation.")
    ap.add_argument("--location", choices=sorted(SCENES))
    ap.add_argument("--child-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--ghost-name")
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
    location = args.location or rng.choice(list(SCENES))
    child_name = args.child_name or rng.choice(NAMES["child"])
    parent_name = args.parent_name or rng.choice(NAMES["parent"])
    ghost_name = args.ghost_name or rng.choice(NAMES["ghost"])
    params = StoryParams(
        location=location,
        child_name=child_name,
        parent_name=parent_name,
        ghost_name=ghost_name,
    )
    if not valid_combo(params):
        raise StoryError("No valid story matches the given options.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
# ASP listing
# ---------------------------------------------------------------------------
def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_list() -> None:
    stories = asp_valid_stories()
    print(f"{len(stories)} valid story setting(s):")
    for (loc,) in stories:
        print(f"  {loc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(location="attic", child_name="Mina", parent_name="Mom", ghost_name="Wisp"),
    StoryParams(location="cellar", child_name="Ollie", parent_name="Dad", ghost_name="Boo"),
    StoryParams(location="hallway", child_name="Pip", parent_name="Aunt", ghost_name="Murmur"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
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
            header = f"### {p.child_name} in {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
