#!/usr/bin/env python3
"""
A tiny mythic storyworld about conjunction and teamwork.

Luna and her companions must join three separated paths with a conjunction of
hands, voices, and courage so the Moon Bridge can be repaired before dawn.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def note(self, text: str) -> None:
        self.trace.append(text)


@dataclass(frozen=True)
class Myth:
    id: str
    realm: str
    obstacle: str
    treasure: str
    omen: str
    ending: str


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    gift: str


MYTHS = {
    "moon_bridge": Myth(
        "moon_bridge",
        "the silver valley",
        "a broken bridge of moonstone",
        "the lost morning bell",
        "three stars blinked above the chasm",
        "the bell rang over the waking hills",
    ),
    "sun_gate": Myth(
        "sun_gate",
        "the amber desert",
        "a sealed gate of golden glass",
        "the first sunrise seed",
        "the horizon darkened before dawn",
        "the gate opened and warm light poured through",
    ),
    "rain_well": Myth(
        "rain_well",
        "the cloud forest",
        "a dry well guarded by a sleeping cloud",
        "the river pearl",
        "the leaves whispered for water",
        "rain sang down upon the thirsty forest",
    ),
}

TOOLS = {
    "ribbon": Tool("ribbon", "a long red ribbon", "a bright thread that could bind"),
    "rope": Tool("rope", "a braided sky-rope", "a strong cord that could hold"),
    "vines": Tool("vines", "three green vines", "living cords that could grow together"),
}

NAMES = {
    "luna": ("Luna", "girl"),
    "orion": ("Orion", "boy"),
    "mira": ("Mira", "girl"),
    "sol": ("Sol", "boy"),
    "tavi": ("Tavi", "boy"),
    "naya": ("Naya", "girl"),
}

ROLES = ["keeper", "climber", "caller"]
SAFE_MIN = 1


@dataclass
class StoryParams:
    myth: str
    tool: str
    leader: str
    helper_one: str
    helper_two: str
    leader_role: str
    helper_one_role: str
    helper_two_role: str
    conjunction: str = "and"
    seed: int | None = None


ASP_RULES = r"""
connected(X,Y) :- joins(X,Y).
connected(X,Y) :- joins(Y,X).
team_ready :- member(A), member(B), member(C), A != B, A != C, B != C,
              connected(A,B), connected(B,C).
valid_story :- team_ready, has_tool.
#show valid_story/0.
"""


def build_world(params: StoryParams) -> World:
    if params.conjunction.strip().lower() != "and":
        raise StoryError("This myth requires the conjunction 'and' to join the team's actions.")
    myth = MYTHS[params.myth]
    tool = TOOLS[params.tool]
    world = World()
    luna = world.add(Entity("leader", "character", params.leader))
    one = world.add(Entity("helper_one", "character", params.helper_one))
    two = world.add(Entity("helper_two", "character", params.helper_two))
    bridge = world.add(Entity("obstacle", "place", myth.obstacle))
    artifact = world.add(Entity("treasure", "object", myth.treasure))
    gear = world.add(Entity("tool", "object", tool.label))

    for person in (luna, one, two):
        person.memes["trust"] = 1.0
        person.memes["courage"] = 1.0
    bridge.meters["broken"] = 1.0
    world.facts.update(myth=myth, tool=tool, people=(luna, one, two), bridge=bridge, artifact=artifact, gear=gear)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    myth: Myth = world.facts["myth"]
    tool: Tool = world.facts["tool"]
    a, b, c = world.facts["people"]
    bridge = world.facts["bridge"]

    world.note(
        f"In {myth.realm}, {a.id} found {myth.obstacle}. "
        f"{myth.omen.capitalize()}."
    )
    world.note(
        f'"I cannot cross it alone," said {a.id}. '
        f'"Then we will cross it together," said {b.id}.'
    )
    world.note(
        f'{c.id} lifted {tool.label}. "{c.id} can bind the broken stones," '
        f'{c.id} said.'
    )

    for person in (a, b, c):
        person.memes["trust"] += 1
        person.memes["courage"] += 1

    world.note(
        f"{a.id} held the first stone, {b.id} held the second, "
        f"and {c.id} tied them with {tool.gift}."
    )
    world.note(
        f"They pulled, pressed, and sang together: "
        f'"One hand, and another, and another!"'
    )

    bridge.meters["broken"] = 0.0
    bridge.meters["joined"] = 1.0
    world.facts["repaired"] = True

    world.note(
        f"The stones answered their shared strength. The path became whole, "
        f"and {a.id}, {b.id}, and {c.id} crossed as one team."
    )
    world.note(
        f"Beyond the bridge they found {myth.treasure}. "
        f"{myth.ending.capitalize()}."
    )
    world.facts["conjunction"] = params.conjunction
    return world


def generation_prompts(world: World) -> list[str]:
    myth: Myth = world.facts["myth"]
    tool: Tool = world.facts["tool"]
    a, b, c = world.facts["people"]
    return [
        f"Tell a myth about {a.id}, {b.id}, and {c.id} repairing {myth.obstacle} through teamwork.",
        f"Write a child-facing myth where the heroes use the conjunction 'and' to join their actions: one holds, one helps, and one binds with {tool.label}.",
        f"Create a story in which a broken path becomes whole because three friends trust one another.",
    ]


def story_qa(world: World) -> list[QAItem]:
    myth: Myth = world.facts["myth"]
    tool: Tool = world.facts["tool"]
    a, b, c = world.facts["people"]
    return [
        QAItem(
            "Who worked together in the myth?",
            f"{a.id}, {b.id}, and {c.id} worked together as a team.",
        ),
        QAItem(
            f"What stood in the heroes' way?",
            f"{myth.obstacle.capitalize()} stood in their way in {myth.realm}.",
        ),
        QAItem(
            "How did the team repair the broken path?",
            f"{a.id} held one stone, {b.id} held another, and {c.id} used {tool.label} to bind them.",
        ),
        QAItem(
            "What conjunction joined the team's actions?",
            "The conjunction 'and' joined the actions: one hero held, another helped, and the third bound.",
        ),
        QAItem(
            "What changed at the end?",
            f"The broken path became whole, so the team could cross and find {myth.treasure}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is teamwork?",
            "Teamwork is when people help one another toward the same goal.",
        ),
        QAItem(
            "What is a conjunction?",
            "A conjunction is a word such as 'and' that joins words or ideas.",
        ),
        QAItem(
            "Why can teamwork solve a hard problem?",
            "Teamwork combines people's strengths, so a job that is too hard for one person may become possible together.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=" ".join(world.trace),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters}, memes={memes}")
    lines.append("events:")
    lines.extend(f"  - {event}" for event in world.trace)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_bridge", "ribbon", "Luna", "Orion", "Mira", "keeper", "climber", "caller"),
    StoryParams("sun_gate", "rope", "Mira", "Sol", "Tavi", "caller", "keeper", "climber"),
    StoryParams("rain_well", "vines", "Luna", "Naya", "Orion", "climber", "caller", "keeper"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a myth about conjunction and teamwork.")
    parser.add_argument("--myth", choices=sorted(MYTHS))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--conjunction", default="and")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.conjunction != "and":
        raise StoryError("Only the conjunction 'and' is supported in this teamwork myth.")
    myth = args.myth or rng.choice(sorted(MYTHS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    names = rng.sample(list(NAMES.values()), 3)
    return StoryParams(
        myth=myth,
        tool=tool,
        leader=names[0][0],
        helper_one=names[1][0],
        helper_two=names[2][0],
        leader_role=rng.choice(ROLES),
        helper_one_role=rng.choice(ROLES),
        helper_two_role=rng.choice(ROLES),
        conjunction=args.conjunction,
    )


def asp_program(extra: str = "", show: str = "#show valid_story/0.") -> str:
    import asp
    facts = [
        asp.fact("member", "leader"),
        asp.fact("member", "helper_one"),
        asp.fact("member", "helper_two"),
        asp.fact("joins", "leader", "helper_one"),
        asp.fact("joins", "helper_one", "helper_two"),
        asp.fact("has_tool"),
    ]
    return "\n".join(facts) + "\n" + ASP_RULES + "\n" + extra + "\n" + show


def verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = bool(asp.atoms(model, "valid_story"))
    if not valid:
        print("FAIL: ASP rejected the teamwork structure.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("repaired"):
            print("FAIL: generated story did not repair the obstacle.")
            return 1
        if " and " not in sample.story:
            print("FAIL: conjunction missing from story.")
            return 1
    print("OK: teamwork, conjunction, ASP, and generated stories agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("valid_story:", bool(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### myth {index + 1}")
        print(sample.story)
        if args.trace and sample.world:
            print(dump_trace(sample.world))
        if args.qa:
            print(format_qa(sample))
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
