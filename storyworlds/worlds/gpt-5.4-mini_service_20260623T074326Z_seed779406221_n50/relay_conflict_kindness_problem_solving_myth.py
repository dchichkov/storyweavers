#!/usr/bin/env python3
"""
storyworlds/worlds/relay_conflict_kindness_problem_solving_myth.py
==================================================================

A small myth-style storyworld about a relay race, a conflict, a kind choice,
and a problem solved together.

Seed premise:
- A relay baton is lost during a mythic race.
- Two runners clash over blame.
- Kindness and problem solving repair the race.
- The ending proves what changed in the world state.

The world uses typed entities with physical meters and emotional memes, a
deterministic state machine, and an inline ASP twin for parity checking.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    team: str = "sun runners"
    conflict: str = "blame"
    kindness: str = "help"
    problem: str = "lost baton"
    setting: str = "hill path"
    relay: str = "relay"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _spread_conflict(world: World) -> None:
    a = world.get("runner_a")
    b = world.get("runner_b")
    baton = world.get("baton")
    if baton.meters.get("lost", 0) >= THRESHOLD and ("spread",) not in world.fired:
        world.fired.add(("spread",))
        a.memes["anger"] = a.memes.get("anger", 0) + 1
        b.memes["anger"] = b.memes.get("anger", 0) + 1
        world.get("path").meters["trouble"] = world.get("path").meters.get("trouble", 0) + 1


def propagate(world: World) -> None:
    _spread_conflict(world)


def setup_world(params: StoryParams) -> World:
    w = World()
    w.add(Entity(id="runner_a", kind="character", type="child", label="first runner", role="runner"))
    w.add(Entity(id="runner_b", kind="character", type="child", label="second runner", role="runner"))
    w.add(Entity(id="path", kind="place", type="path", label=params.setting))
    w.add(Entity(id="baton", kind="thing", type="baton", label="golden baton", role="relay object"))
    w.add(Entity(id="torch", kind="thing", type="light", label="torch of dawn"))
    w.get("runner_a").memes["pride"] = 1
    w.get("runner_b").memes["pride"] = 1
    w.get("path").meters["trouble"] = 0
    w.get("baton").meters["lost"] = 1
    w.facts["params"] = params
    return w


def tell(params: StoryParams) -> World:
    w = setup_world(params)
    a = w.get("runner_a")
    b = w.get("runner_b")
    baton = w.get("baton")
    path = w.get("path")

    w.say(
        f"Long ago, on the {params.setting}, the {params.team} began a {params.relay} "
        f"like a little myth of speed."
    )
    w.say(
        f"The runners carried a {baton.label}, and when it slipped from hand to hand "
        f"it vanished into the dust."
    )
    w.para()

    a.memes["anger"] = a.memes.get("anger", 0) + 1
    b.memes["anger"] = b.memes.get("anger", 0) + 1
    w.say(
        f"Then conflict rose. {a.label.capitalize()} blamed {b.label}, and {b.label} "
        f"blamed {a.label}."
    )
    propagate(w)
    w.say(
        f"The whole path felt tighter and stormier, because the lost baton made the "
        f"race stall."
    )
    w.para()

    b.memes["kindness"] = b.memes.get("kindness", 0) + 1
    w.say(
        f"But {b.label} chose kindness instead of sharper words. {b.id.replace('_', ' ').capitalize()} "
        f"knelt, brushed dust away, and pointed to the tracks in the dirt."
    )
    w.say(
        f"Together they used problem solving: one runner searched near the stones while "
        f"the other retraced the last exchange."
    )
    baton.meters["lost"] = 0
    baton.meters["found"] = 1
    path.meters["trouble"] = 0
    a.memes["relief"] = a.memes.get("relief", 0) + 1
    b.memes["relief"] = b.memes.get("relief", 0) + 1
    w.para()

    w.say(
        f"At last the {baton.label} was found, bright as a small star in the dust."
    )
    w.say(
        f"The {params.team} finished the {params.relay} side by side, wiser than before, "
        f"and the hill path grew quiet again."
    )

    w.facts.update(
        params=params,
        baton=baton,
        path=path,
        outcome="repaired",
    )
    return w


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What kind of event was the story about?",
            answer=f"It was about a {p.relay} on the {p.setting}.",
        ),
        QAItem(
            question="What problem caused the conflict?",
            answer="The golden baton was lost, so the runners started blaming each other.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer="They calmed down, searched together, and found the baton in the dust.",
        ),
        QAItem(
            question="What kindness helped the story turn around?",
            answer="One runner stopped blaming and chose to help the other look for tracks.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a relay?",
            answer="A relay is a race where runners take turns passing a baton to one another.",
        ),
        QAItem(
            question="Why is kindness useful during a conflict?",
            answer="Kindness helps people stop blaming and start listening, which makes solving the problem easier.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking carefully at a trouble and choosing a way to fix it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a myth-like story about a {p.relay} on the {p.setting} where a lost baton causes conflict.",
        "Include a kind turn where the runners stop blaming each other and solve the problem together.",
        "End with the baton found and the team finishing the race changed by what they learned.",
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
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        parts.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(parts)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic relay conflict/kindness/problem-solving storyworld.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        team=rng.choice(["sun runners", "river runners", "star runners"]),
        conflict="blame",
        kindness="help",
        problem="lost baton",
        setting=rng.choice(["hill path", "marble track", "sunlit bridge"]),
        relay="relay",
        seed=args.seed,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("relay", "relay"),
            asp.fact("conflict", "blame"),
            asp.fact("kindness", "help"),
            asp.fact("problem", "lost_baton"),
        ]
    )


ASP_RULES = r"""
ok_story :- relay(relay), conflict(blame), kindness(help), problem(lost_baton).
#show ok_story/0.
"""


def asp_program(extra: str = "", show: str = "#show ok_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_ok() -> bool:
    import asp
    model = asp.one_model(asp_program())
    return any(sym.name == "ok_story" for sym in model)


def asp_verify() -> int:
    return 0 if asp_ok() else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(resolve_params(args, rng)) for _ in range(args.n)]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
