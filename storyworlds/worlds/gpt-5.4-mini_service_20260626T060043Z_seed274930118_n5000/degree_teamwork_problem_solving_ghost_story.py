#!/usr/bin/env python3
"""
storyworlds/worlds/degree_teamwork_problem_solving_ghost_story.py
=================================================================

A small ghost-story world with teamwork and problem-solving around a
degree ceremony.

Seed premise:
---
A nervous child wants a degree from the old moonlit school, but the hall is
haunted by a puzzled ghost who cannot open the sealed archive. The child and
the ghost work together, solve the problem, and uncover the forgotten key so
the degree can finally be awarded.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "fear": 0.0, "closeness": 0.0, "progress": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "teamwork": 0.0, "relief": 0.0}


@dataclass
class Setting:
    place: str = "the old school"
    moonlit: bool = True
    affords: set[str] = field(default_factory=lambda: {"archive", "bell", "lantern"})


@dataclass
class Puzzle:
    id: str
    problem: str
    clue: str
    fix: str
    action: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Degree:
    label: str = "degree"
    phrase: str = "a folded paper degree with a blue ribbon"
    type: str = "degree"
    require: str = "archive"


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    solves: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.facts = dict(self.facts)
        return c


def pronoun(entity: Entity, case: str = "subject") -> str:
    female = {"girl", "mother", "woman"}
    male = {"boy", "father", "man"}
    if entity.type in female:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if entity.type in male:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "it", "object": "it", "possessive": "its"}[case]


def label_word(entity: Entity) -> str:
    return {"mother": "mom", "father": "dad"}.get(entity.type, entity.type)


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("archive_opened"):
        return out
    for actor in world.characters():
        if actor.meters["progress"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id:
                continue
            sig = ("dust", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            out.append(f"The old air left a thin layer of dust on {item.label}.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("solution_found"):
        return out
    for actor in world.characters():
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["relief"] += 1
        actor.memes["worry"] = max(0.0, actor.memes["worry"] - 1.0)
        out.append(f"{actor.id} felt the tight worry loosen in {actor.chest if hasattr(actor, 'chest') else 'their chest'}.")
    return out


CAUSAL_RULES = [
    _r_dust,
    _r_relief,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting()

PUZZLES = {
    "sealed_archive": Puzzle(
        id="sealed_archive",
        problem="the archive door is sealed shut",
        clue="a silver key is hidden in the bell tower",
        fix="work together to find the key and open the archive",
        action="search the tower and open the archive",
        resolution="the archive door swings open",
        tags={"archive", "key", "teamwork", "problem_solving"},
    ),
    "flickering_lantern": Puzzle(
        id="flickering_lantern",
        problem="the hallway lantern keeps flickering out",
        clue="a draft is blowing through a cracked window",
        fix="block the draft and light the lantern together",
        action="fix the window and relight the lantern",
        resolution="the hallway glows steady and bright",
        tags={"lantern", "window", "teamwork", "problem_solving"},
    ),
}

DEGREES = {
    "paper_degree": Degree(),
}

TOOLS = [
    Tool(
        id="lantern",
        label="a brass lantern",
        covers={"dark"},
        solves={"flicker", "search"},
        prep="pick up the lantern and look carefully",
        tail="held the lantern high while they searched",
    ),
    Tool(
        id="rope",
        label="a long rope",
        covers={"tower"},
        solves={"climb", "pull"},
        prep="tie the rope to the rail",
        tail="used the rope to climb safely",
    ),
    Tool(
        id="chalk_map",
        label="a chalk map",
        covers={"clue"},
        solves={"find", "mark"},
        prep="draw the halls on the chalk map",
        tail="followed the chalk marks like breadcrumbs",
    ),
]

HEROES = [
    ("Mina", "girl"),
    ("Noah", "boy"),
    ("Iris", "girl"),
    ("Theo", "boy"),
]

GHOSTS = [
    ("Murmur", "ghost"),
    ("Pale Pip", "ghost"),
    ("Luna Drift", "ghost"),
]


@dataclass
class StoryParams:
    puzzle: str
    degree: str
    hero_name: str
    hero_type: str
    ghost_name: str
    seed: Optional[int] = None


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost"))
    degree = world.add(Entity(
        id="degree",
        type="degree",
        label="degree",
        phrase=DEGREES[params.degree].phrase,
        owner=hero.id,
    ))
    archive = world.add(Entity(id="archive", type="door", label="archive door"))
    key = world.add(Entity(id="key", type="thing", label="silver key"))

    hero.memes.update({"hope": 1.0, "worry": 1.0, "teamwork": 0.0, "relief": 0.0})
    ghost.memes.update({"hope": 0.5, "worry": 1.0, "teamwork": 0.0, "relief": 0.0})

    p = PUZZLES[params.puzzle]

    world.say(f"{hero.id} was a quiet little {hero.type} who wanted a {degree.label}.")
    world.say(f"At the old school, {hero.id} found {ghost.id}, a moon-pale ghost who could not open the archive.")
    world.say(f"The problem was simple to say but hard to solve: {p.problem}.")
    world.para()
    world.say(f"{ghost.id} whispered that {p.clue}.")
    world.say(f"{hero.id} did not run away. Instead, {pronoun(hero).capitalize()} said they could solve it together.")
    hero.memes["teamwork"] += 1.0
    ghost.memes["teamwork"] += 1.0

    tool = world.add(Entity(id="lantern_item", type="tool", label="brass lantern", owner=hero.id))
    tool.worn_by = hero.id

    if params.puzzle == "sealed_archive":
        world.say("First they took a lantern to the tower so the steps would not swallow their feet.")
        world.say("Then the ghost lifted the dusty curtain and the child noticed the silver key tucked behind a loose stone.")
        key.owner = hero.id
        world.facts["key_found"] = True
        world.facts["archive_opened"] = True
        hero.meters["progress"] += 1.0
        ghost.meters["progress"] += 1.0
        propagate(world, narrate=True)
        world.say(f"Together they unlocked the archive and the heavy door yawned open with a soft creak.")
        world.say(f"Inside, the old paper degree waited on a velvet cushion, and {hero.id} held it with careful hands.")
        world.facts["solution_found"] = True
    else:
        world.say("They found the cracked window, blocked the draft with a folded cloak, and lit the lantern again.")
        hero.meters["progress"] += 1.0
        ghost.meters["progress"] += 1.0
        world.facts["archive_opened"] = True
        world.facts["solution_found"] = True
        propagate(world, narrate=True)
        world.say(f"The hallway glowed steady and bright, and the ghost smiled as the whole school stopped shivering.")
        world.say(f"With the problem solved, the degree could be given at last.")

    world.para()
    hero.memes["worry"] = 0.0
    ghost.memes["worry"] = 0.0
    world.say(f"{hero.id} smiled, and {ghost.id} bowed like a proud teacher from an older time.")
    world.say(f"The degree was not just a paper thing anymore; it was proof that they had solved a hard problem together.")

    world.facts.update(hero=hero, ghost=ghost, degree=degree, puzzle=p, archive=archive, key=key)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a child about {f["hero"].id}, a {f["hero"].type}, who wants a {f["degree"].label}.',
        f'Tell a spooky but gentle story where {f["hero"].id} and {f["ghost"].id} use teamwork to solve {f["puzzle"].problem}.',
        f'Write a simple moonlit school story that ends with a {f["degree"].label} after a problem is solved together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    degree = f["degree"]
    p = f["puzzle"]
    return [
        QAItem(
            question=f"What did {hero.id} want in the old school?",
            answer=f"{hero.id} wanted a {degree.label} from the haunted school.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{ghost.id}, a gentle ghost, helped {hero.id} solve it with teamwork.",
        ),
        QAItem(
            question=f"What was the hard problem in the story?",
            answer=f"The hard problem was that {p.problem}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {ghost.id} fix the problem?",
            answer=f"They worked together to {p.fix}.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, {p.resolution}, and {hero.id} could hold the {degree.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost?",
            answer="A ghost is a spooky story character often described as the spirit of someone who lived long ago.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help each other to reach the same goal.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a way to fix something that is hard or stuck.",
        ),
        QAItem(
            question="What is a degree?",
            answer="A degree is a certificate or award that shows someone finished a course of learning.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- character(X).
ghost(X) :- type(X,ghost).

teamwork(H,G) :- character(H), type(G,ghost), helps(G,H).
problem_solved(P) :- puzzle(P), clue_found(P), fix_done(P).
degree_awarded(D) :- degree(D), problem_solved(_), teamwork(_, _).

#show hero/1.
#show ghost/1.
#show teamwork/2.
#show problem_solved/1.
#show degree_awarded/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hero_name, hero_type in HEROES:
        lines.append(asp.fact("character", hero_name))
        lines.append(asp.fact("type", hero_name, hero_type))
    for ghost_name, _ in GHOSTS:
        lines.append(asp.fact("character", ghost_name))
        lines.append(asp.fact("type", ghost_name, "ghost"))
    for pid in PUZZLES:
        lines.append(asp.fact("puzzle", pid))
    for did in DEGREES:
        lines.append(asp.fact("degree", did))
    lines.append(asp.fact("helps", "Murmur", "Mina"))
    lines.append(asp.fact("helps", "Pale Pip", "Noah"))
    lines.append(asp.fact("helps", "Luna Drift", "Iris"))
    lines.append(asp.fact("helps", "Luna Drift", "Theo"))
    lines.append(asp.fact("clue_found", "sealed_archive"))
    lines.append(asp.fact("fix_done", "sealed_archive"))
    lines.append(asp.fact("clue_found", "flickering_lantern"))
    lines.append(asp.fact("fix_done", "flickering_lantern"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show degree_awarded/1.\n#show teamwork/2.\n#show problem_solved/1."))
    if model:
        print("OK: ASP program is grounded and solvable.")
        return 0
    print("MISMATCH: ASP program produced no model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about teamwork, problem solving, and a degree.")
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--degree", choices=DEGREES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--ghost-name")
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
    puzzle = args.puzzle or rng.choice(list(PUZZLES))
    degree = args.degree or "paper_degree"
    hero_name, hero_type = rng.choice(HEROES)
    ghost_name, _ = rng.choice(GHOSTS)
    if args.hero_name:
        hero_name = args.hero_name
    if args.hero_type:
        hero_type = args.hero_type
    if args.ghost_name:
        ghost_name = args.ghost_name
    return StoryParams(
        puzzle=puzzle,
        degree=degree,
        hero_name=hero_name,
        hero_type=hero_type,
        ghost_name=ghost_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        print(asp_program("#show degree_awarded/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show degree_awarded/1.\n#show teamwork/2.\n#show problem_solved/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for puzzle in PUZZLES:
            params = StoryParams(
                puzzle=puzzle,
                degree="paper_degree",
                hero_name="Mina" if puzzle == "sealed_archive" else "Iris",
                hero_type="girl",
                ghost_name="Murmur" if puzzle == "sealed_archive" else "Luna Drift",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
