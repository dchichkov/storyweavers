#!/usr/bin/env python3
"""
A small detective-story world about a tiny clue, a stuck hinge, and a turnip
that helps friendship solve the case.

The seed image for this world is a child-facing detective tale:
a squirrel-dim whisper of trouble in a garden, a squeaky hinge on a shed, and
a missing turnip that turns out to matter because of friendship.
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

RNG_NAMES = [
    "Nina", "Milo", "Tessa", "Owen", "Pip", "June", "Arlo", "Mina", "Ezra", "Luna",
]
RNG_HELPERS = [
    "friend", "neighbor", "classmate",
]
RNG_TRAITS = [
    "curious", "kind", "careful", "bright", "patient", "gentle",
]
RNG_SETTINGS = [
    "the garden", "the yard", "the little farm path", "the shed door", "the market stall",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    discovered_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "rust": 0.0, "missing": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "friendship": 0.0, "relief": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
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


@dataclass
class StoryParams:
    setting: str
    name: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
#show clue/2.
#show solved/1.

clue(hinge, stuck) :- hinge_state(stuck).
clue(turnip, hidden) :- turnip_state(hidden).
solved(case) :- clue(hinge, stuck), clue(turnip, hidden), friendship(shared).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hinge_state", "stuck"),
            asp.fact("turnip_state", "hidden"),
            asp.fact("friendship", "shared"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name or not params.friend_name:
        raise StoryError("Both the detective and a friend are needed for this friendship case.")
    if params.name == params.friend_name:
        raise StoryError("The detective and the friend must be different people.")
    if not params.setting:
        raise StoryError("A setting is required for the case.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world about a hinge, a turnip, and friendship.")
    ap.add_argument("--setting", choices=RNG_SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=RNG_TRAITS)
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
    setting = args.setting or rng.choice(RNG_SETTINGS)
    name = args.name or rng.choice(RNG_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in RNG_NAMES if n != name])
    trait = args.trait or rng.choice(RNG_TRAITS)
    params = StoryParams(setting=setting, name=name, friend_name=friend_name, trait=trait)
    reasonableness_gate(params)
    return params


def make_world(params: StoryParams) -> World:
    world = World(setting=params.setting)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        label=params.name,
        phrase=f"a {params.trait} detective named {params.name}",
        tags={"detective", "friendship"},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        label=params.friend_name,
        phrase=f"a good friend named {params.friend_name}",
        tags={"friend", "friendship"},
    ))
    hinge = world.add(Entity(
        id="hinge",
        kind="thing",
        label="hinge",
        phrase="a squeaky hinge on the little door",
        meters={"rust": 1.0, "dust": 1.0, "missing": 0.0},
        memes={"worry": 0.0, "friendship": 0.0, "relief": 0.0, "curiosity": 0.0},
        tags={"hinge", "clue"},
    ))
    turnip = world.add(Entity(
        id="turnip",
        kind="thing",
        label="turnip",
        phrase="a round white turnip from the garden box",
        owner="gardener",
        discovered_by=None,
        meters={"dust": 0.0, "rust": 0.0, "missing": 1.0},
        memes={"worry": 0.0, "friendship": 0.0, "relief": 0.0, "curiosity": 0.0},
        tags={"turnip", "clue"},
    ))
    world.facts.update(
        detective=detective,
        friend=friend,
        hinge=hinge,
        turnip=turnip,
        setting=params.setting,
    )
    return world


def narrate(world: World) -> None:
    d = world.get("detective")
    f = world.get("friend")
    hinge = world.get("hinge")
    turnip = world.get("turnip")

    world.say(
        f"One afternoon, {d.label} walked through {world.setting} with a notebook and a sharp eye. "
        f"{d.label} was the kind of detective who noticed little things, even a squirrel-dim shadow under a bush."
    )
    world.say(
        f"Then {f.label} hurried over and whispered about a missing turnip. "
        f"That sounded odd, because the only clue nearby was {hinge.phrase}, which squeaked like a tiny mouse."
    )

    world.para()
    d.memes["curiosity"] += 1
    f.memes["worry"] += 1
    hinge.meters["rust"] += 0.5
    world.say(
        f"{d.label} knelt beside the hinge and listened. The squeak pointed toward the garden box, not the gate. "
        f"{f.label} helped by looking under leaves and behind stones, which made the search feel like a team job."
    )
    turnip.meters["missing"] = 0.0
    turnip.discovered_by = "friend"
    world.facts["clue_chain"] = ["hinge", "garden_box", "turnip"]

    world.para()
    d.memes["friendship"] += 1
    f.memes["friendship"] += 1
    d.memes["relief"] += 1
    f.memes["relief"] += 1
    world.say(
        f"At last, {f.label} found the turnip tucked safely inside an old basket near the shed. "
        f"The basket had bumped against the hinge, and that was why the clue had felt so small and strange."
    )
    world.say(
        f"{d.label} smiled and wrote the case closed. "
        f"{d.label} and {f.label} carried the turnip back together, and the squeaky hinge suddenly sounded less lonely."
    )


def story_qa(world: World) -> list[QAItem]:
    d = world.get("detective")
    f = world.get("friend")
    return [
        QAItem(
            question=f"Who solved the little case in {world.setting}?",
            answer=f"{d.label} solved it with help from {f.label}.",
        ),
        QAItem(
            question="What made the clue seem tiny at first?",
            answer="The hinge only squeaked a little, so the clue felt small and easy to miss.",
        ),
        QAItem(
            question="Where was the turnip found?",
            answer="The turnip was found tucked safely inside an old basket near the shed.",
        ),
        QAItem(
            question="Why did the detective trust the friend?",
            answer=f"{d.label} trusted {f.label} because they worked together and showed friendship while searching.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hinge?",
            answer="A hinge is the part that lets a door or gate swing open and shut.",
        ),
        QAItem(
            question="What is a turnip?",
            answer="A turnip is a round root vegetable that grows in the ground and can be dug up from a garden.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and working together kindly.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    d = world.get("detective")
    f = world.get("friend")
    return [
        f"Write a short detective story for a child about {d.label}, {f.label}, a squeaky hinge, and a missing turnip.",
        f"Tell a gentle mystery where {d.label} follows a squirrel-dim clue and friendship helps solve the case.",
        f"Write a simple story set in {world.setting} where a hinge clue leads to a turnip and a happy ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


CURATED = [
    StoryParams(setting="the garden", name="Nina", friend_name="Milo", trait="curious"),
    StoryParams(setting="the yard", name="Tessa", friend_name="Owen", trait="careful"),
    StoryParams(setting="the shed door", name="Pip", friend_name="June", trait="kind"),
]


def asp_verify() -> int:
    import asp
    program = asp_program("#show solved/1.")
    model = asp.one_model(program)
    solved = set(asp.atoms(model, "solved"))
    expected = {("case",)}
    if solved == expected:
        print("OK: ASP twin marks the case solved.")
        return 0
    print("MISMATCH: ASP twin did not solve the case.")
    print("  model:", sorted(solved))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
