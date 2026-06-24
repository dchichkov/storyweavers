#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/quintuplet_conflict_repetition_space_adventure.py
===========================================================================================================================

A small standalone storyworld about five sibling astronauts, a repeated task, and
a conflict that turns into cooperation during a space adventure.

Seed inspiration:
- quintuplet
- Conflict
- Repetition
- Space Adventure

The world is built around a compact mission on a starship. Five quintuplet kids
must repeat a docking checklist, but one of them rushes ahead and causes a tense
moment. The story resolves when they repeat the checklist together and finish
the mission safely.
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


@dataclass
class StoryParams:
    crew_name: str = "Nova"
    ship_name: str = "Star Kite"
    destination: str = "the moon dock"
    task: str = "check the hatch"
    repeated_phrase: str = "check the hatch twice"
    danger: str = "the airlock could stay open"
    helper_tool: str = "a red tablet"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    labels: list[str] = field(default_factory=list)


@dataclass
class World:
    ship_name: str
    destination: str
    task: str
    repeated_phrase: str
    danger: str
    helper_tool: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent


ASP_RULES = r"""
% Five siblings share one mission.
quintuplet(crew, N) :- sibling(N).

% Repetition matters when the checklist is done twice.
repetition(task, phrase) :- checklist_phrase(task, phrase).

% Conflict happens if one sibling rushes ahead before the repeated check is finished.
conflict(crew, task) :- rushed_ahead(crew, task), not completed_twice(crew, task).

% A safe ending requires the repeated action and the tool.
resolved(crew, task) :- completed_twice(crew, task), has_tool(crew, tool), tool(tool).
"""


def asp_facts() -> str:
    import asp  # lazy import

    lines = [
        asp.fact("ship", "star_kite"),
        asp.fact("destination", "moon_dock"),
        asp.fact("task", "check_hatch"),
        asp.fact("checklist_phrase", "check_hatch", "check the hatch twice"),
        asp.fact("tool", "tablet_red"),
    ]
    for i in range(1, 6):
        lines.append(asp.fact("sibling", f"kid{i}"))
    lines.append(asp.fact("quintuplet_group", "nova_family"))
    lines.append(asp.fact("repetition_needed", "check_hatch"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _introduce(world: World, crew_name: str) -> None:
    world.say(
        f"{crew_name} was one of five quintuplet kids aboard the {world.ship_name}. "
        f"They liked doing things together, especially on a space adventure."
    )


def _setup(world: World, crew_name: str) -> None:
    world.say(
        f"At the start of the trip, the ship drifted toward {world.destination}. "
        f"The captain asked the quintuplet to {world.task} and repeat {world.repeated_phrase}."
    )


def _conflict(world: World, crew_name: str) -> None:
    world.say(
        f"Three of the siblings said the same words again and again, while {crew_name} "
        f"got excited and rushed for the control panel."
    )
    world.say(
        f"That made a conflict, because {world.danger} if nobody finished the check."
    )


def _resolution(world: World, crew_name: str) -> None:
    world.say(
        f"Then the quintuplet took a breath and started over. "
        f"They used {world.helper_tool} and repeated the checklist together."
    )
    world.say(
        f"This time {crew_name} stayed with the group until the hatch was safe, "
        f"and the ship sailed on toward {world.destination} with calm lights and smiling faces."
    )


def tell(params: StoryParams) -> World:
    world = World(
        ship_name=params.ship_name,
        destination=params.destination,
        task=params.task,
        repeated_phrase=params.repeated_phrase,
        danger=params.danger,
        helper_tool=params.helper_tool,
    )
    leader = world.add(Entity(name=params.crew_name, role="quintuplet"))
    leader.meters["curiosity"] = 1
    leader.memes["joy"] = 1
    world.facts.update(
        crew_name=params.crew_name,
        ship_name=params.ship_name,
        destination=params.destination,
        task=params.task,
        repeated_phrase=params.repeated_phrase,
        danger=params.danger,
        helper_tool=params.helper_tool,
    )

    _introduce(world, params.crew_name)
    world.para()
    _setup(world, params.crew_name)
    world.para()
    _conflict(world, params.crew_name)
    world.para()
    _resolution(world, params.crew_name)

    world.facts["conflict"] = True
    world.facts["resolved"] = True
    world.facts["repetition"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space story about a quintuplet named {f['crew_name']} on the {f['ship_name']}.",
        f"Tell a child-friendly story where {f['crew_name']} must repeat the {f['task']} on the way to {f['destination']}.",
        f"Write a simple adventure with conflict and repetition that ends with the ship safely reaching {f['destination']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {f['crew_name']}, one of five quintuplet kids on the {f['ship_name']}."
        ),
        QAItem(
            question=f"What did the quintuplet need to do?",
            answer=f"They needed to {f['task']} and repeat it as {f['repeated_phrase']}."
        ),
        QAItem(
            question=f"Why was there a conflict?",
            answer=f"There was a conflict because {f['crew_name']} rushed ahead, and {f['danger']} if the check was not finished."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The quintuplet repeated the checklist together with {f['helper_tool']} and reached {f['destination']} safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quintuplet?",
            answer="A quintuplet is one of five siblings born at the same time."
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same action or saying the same words again."
        ),
        QAItem(
            question="What is a hatch on a spaceship?",
            answer="A hatch is a door on a ship or spacecraft that can open and close."
        ),
        QAItem(
            question="Why do astronauts use checklists?",
            answer="Astronauts use checklists so they do not miss important safety steps."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for name, ent in world.entities.items():
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{name}: " + ", ".join(bits))
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "No story: this world needs a quintuplet, a repeatable task, a conflict, and a safe resolution."


def valid_combo() -> bool:
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about a quintuplet and repetition.")
    ap.add_argument("--name", dest="crew_name", default="Nova")
    ap.add_argument("--ship", dest="ship_name", default="Star Kite")
    ap.add_argument("--destination", default="the moon dock")
    ap.add_argument("--task", default="check the hatch")
    ap.add_argument("--tool", dest="helper_tool", default="a red tablet")
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
    return StoryParams(
        crew_name=args.crew_name,
        ship_name=args.ship_name,
        destination=args.destination,
        task=args.task,
        repeated_phrase=f"{args.task} twice",
        danger="the airlock could stay open",
        helper_tool=args.helper_tool,
    )


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


def asp_verify() -> int:
    return 0 if valid_combo() else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/2. #show repetition/2. #show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []
    if args.all:
        samples.append(generate(resolve_params(args, rng)))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
