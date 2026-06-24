#!/usr/bin/env python3
"""
storyworlds/worlds/cedar_bus_depot_suspense_tall_tale.py
========================================================

A standalone storyworld for a small Tall Tale-style suspense at a bus depot.
Seed image: a cedar-scented bus depot, a big tricky wait, and a brave turn
that reveals what changed.

The world is built around:
- a depot full of buses and schedules
- a cedar object or scent that matters in the suspense
- a tense problem that can be solved by careful, physical action
- a tall-tale narrator voice with concrete, child-facing images
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

TITLE = "cedar bus depot suspense tall tale"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Depot:
    name: str = "the bus depot"
    cedar: str = "cedar"
    buses_ready: int = 0
    fog_thick: bool = False
    clock_ticking: bool = True
    lost_item: bool = True
    found_item: bool = False
    safe_departure: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    role: str
    helper: str
    lost_item: str
    seed: Optional[int] = None


NAMES = ["Milo", "June", "Pip", "Ada", "Nell", "Wes", "Zara", "Theo"]
ROLES = ["driver", "dispatcher", "porter", "mechanic"]
HELPERS = ["an old porter", "a steady driver", "a quick dispatcher", "a grandparent"]
LOST_ITEMS = [
    "a red ticket pouch",
    "a brass key ring",
    "a lunch box with a blue lid",
    "a tiny whistle",
]


@dataclass
class World:
    depot: Depot
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(Depot(**self.depot.__dict__))
        clone.entities = {k: Entity(**v.__dict__) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        return clone


ASP_RULES = r"""
% Cedar-scented depot suspense twin.
at_risk(Item) :- lost(Item), fog, ticking.
can_find(Item) :- at_risk(Item), has_light, knows_place.
safe_departure :- can_find(Item), bus_ready.
#show at_risk/1.
#show can_find/1.
#show safe_departure/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("depot", "bus_depot"),
        asp.fact("cedar", "cedar"),
        asp.fact("fog"),
        asp.fact("ticking"),
        asp.fact("has_light"),
        asp.fact("knows_place"),
        asp.fact("bus_ready"),
        asp.fact("lost", "ticket_pouch"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name or not params.helper or not params.lost_item:
        raise StoryError("The depot tale needs a hero, a helper, and a lost item.")


def solve_gate() -> bool:
    import asp
    model = asp.one_model(asp_program())
    return ("safe_departure", ()) in set(asp.atoms(model, "safe_departure"))


def build_world(params: StoryParams) -> World:
    world = World(Depot())
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper))
    item = world.add(Entity(id="lost", kind="thing", type="item", label=params.lost_item))
    world.depot.facts.update(hero=hero, helper=helper, item=item)
    return world


def tell(world: World, params: StoryParams) -> World:
    d = world.depot
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    item = world.entities["lost"]

    world.say(
        f"At the bus depot, the air smelled of cedar, diesel, and rain on old boards."
    )
    world.say(
        f"{hero.label} was waiting beside the ticket window when the clock began to tick like a little hammer."
    )
    world.say(
        f"Every bus was nearly ready, but the fog curled around the bays and hid {params.lost_item} from sight."
    )
    d.fog_thick = True
    d.buses_ready = 3

    world.para()
    world.say(
        f"Then {hero.label} noticed the trouble: {params.lost_item} was gone, and the next bus was due before the kettle could boil."
    )
    world.say(
        f"{helper.label.capitalize()} said, 'Hold steady. Cedar wood remembers a path, and so do sharp eyes.'"
    )
    world.say(
        f"So the two of them listened for the rattle, the scrape, and the tiny click that would give the hiding place away."
    )

    world.para()
    world.say(
        f"{hero.label} followed the cedar scent to the loading ramp, where a crate had rolled just enough to tuck {params.lost_item} behind it."
    )
    world.say(
        f"{helper.label.capitalize()} lifted the crate, and there sat the lost thing, plain as moonlight on a tin roof."
    )
    d.lost_item = False
    d.found_item = True

    world.para()
    world.say(
        f"In a blink, the whistle blew, the doors sighed open, and {hero.label} carried {params.lost_item} back to the counter."
    )
    world.say(
        f"The bus pulled out safe and sound, and the cedar smell stayed in the depot like a quiet guardian after the storm."
    )
    d.safe_departure = True
    world.depot.facts.update(found=True, safe=True)
    return world


def prompts(world: World, params: StoryParams) -> list[str]:
    return [
        f'Write a suspenseful tall tale for children set in a bus depot that includes cedar, a lost item, and a safe ending.',
        f"Tell a big-voiced little story about {params.name} at the bus depot, where {params.lost_item} goes missing and a helper uses keen sense and courage to solve it.",
        f'Create a child-friendly suspense story in a cedar-scented bus depot where the clock is ticking and the hero must act fast.',
    ]


def story_qa(world: World, params: StoryParams) -> list[QAItem]:
    return [
        QAItem(
            question=f"Where does {params.name} wait in the story?",
            answer="They wait at the bus depot, where the buses are getting ready to leave.",
        ),
        QAItem(
            question=f"What was missing when the suspense began?",
            answer=f"{params.lost_item} was missing, and that made the wait feel urgent.",
        ),
        QAItem(
            question="What clue helped find the lost item?",
            answer="The cedar scent helped point the search toward the loading ramp and the crate.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The lost item was found, the bus left safely, and the depot felt calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cedar?",
            answer="Cedar is a kind of wood with a strong, pleasant smell, and people often notice it in boxes, boards, or closets.",
        ),
        QAItem(
            question="What is a bus depot?",
            answer="A bus depot is a place where buses wait, park, and get ready for their trips.",
        ),
        QAItem(
            question="Why can a ticking clock make a scene suspenseful?",
            answer="A ticking clock can make a scene feel suspenseful because everyone knows time is passing and something important may happen soon.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    d = world.depot
    return "\n".join([
        "--- world trace ---",
        f"depot.name={d.name}",
        f"depot.cedar={d.cedar}",
        f"depot.buses_ready={d.buses_ready}",
        f"depot.fog_thick={d.fog_thick}",
        f"depot.lost_item={d.lost_item}",
        f"depot.found_item={d.found_item}",
        f"depot.safe_departure={d.safe_departure}",
    ])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale suspense at a cedar bus depot.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--lost-item", choices=LOST_ITEMS, dest="lost_item")
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
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    helper = args.helper or rng.choice(HELPERS)
    lost_item = args.lost_item or rng.choice(LOST_ITEMS)
    return StoryParams(name=name, role=role, helper=helper, lost_item=lost_item)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world, params),
        story_qa=story_qa(world, params),
        world_qa=world_qa(world),
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
    import asp
    ok = solve_gate()
    if not ok:
        print("ASP gate did not produce safe_departure.")
        return 1
    print("OK: ASP gate produced safe_departure.")
    return 0


CURATED = [
    StoryParams(name="Milo", role="dispatcher", helper="a steady driver", lost_item="a brass key ring"),
    StoryParams(name="June", role="porter", helper="an old porter", lost_item="a red ticket pouch"),
    StoryParams(name="Ada", role="mechanic", helper="a quick dispatcher", lost_item="a tiny whistle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
