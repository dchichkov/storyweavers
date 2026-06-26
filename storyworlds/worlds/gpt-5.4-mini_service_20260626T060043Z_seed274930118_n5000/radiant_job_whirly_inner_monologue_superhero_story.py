#!/usr/bin/env python3
"""
storyworlds/worlds/radiant_job_whirly_inner_monologue_superhero_story.py
========================================================================

A standalone story world for a tiny Superhero Story about a radiant hero,
a stubborn job, and a whirly machine, told with inner monologue.

Premise seed:
- A small city has a job to finish before dusk.
- A young superhero can glow with radiant light.
- A whirly machine keeps tangling the work.
- The hero's inner monologue helps them think through the problem and solve it.

The world is intentionally small and constraint-checked:
- One hero, one helper, one job, one whirly obstacle.
- The story is state-driven, with physical meters and emotional memes.
- Invalid combinations raise StoryError with a clear reason.
- An inline ASP twin mirrors the Python validity gate.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def mget(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def eg(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    acts: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    need: str
    obstacle: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def reasonableness_gate(place: Place, task: Task, gear: Gear) -> bool:
    return task.id in place.acts and task.id in gear.helps and task.zone in gear.covers


def explain_rejection(place: Place, task: Task, gear: Gear) -> str:
    return (
        f"(No story: {task.gerund} at {place.label} cannot be fixed by {gear.label} "
        f"because the gear does not cover the right place or help with the right problem.)"
    )


def _inner_monologue(hero: Entity, task: Task, obstacle_state: str) -> str:
    if obstacle_state == "stuck":
        return (
            f"{hero.pronoun().capitalize()} thought, "
            f'"If I rush, I will only make the whirly mess worse. '
            f'If I slow down and shine on the right spot, I can guide it out."'
        )
    return (
        f"{hero.pronoun().capitalize()} thought, "
        f'"The job looks big, but my radiant light can make the tiny hard parts clear."'
    )


def predict(world: World, hero: Entity, task: Task) -> dict:
    sim = world.copy()
    do_task(sim, sim.get(hero.id), task, narrate=False)
    job = sim.get("job")
    return {"done": job.mget("done") >= THRESHOLD, "tangled": job.mget("tangled") >= THRESHOLD}


def do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    job = world.get("job")
    if job.mget("done") >= THRESHOLD:
        return
    hero.meters["radiant"] = hero.meters.get("radiant", 0.0) + 1.0
    if task.id == "whirly":
        job.meters["tangled"] = job.meters.get("tangled", 0.0) + 1.0
        hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1.0
        if narrate:
            world.say(
                f"A whirly gust spun through the work and tugged at the last pieces."
            )
    job.meters["done"] = job.meters.get("done", 0.0) + 1.0
    if job.meters["done"] >= THRESHOLD:
        world.fired.add(("done", task.id))
        if narrate:
            world.say(
                f"The job clicked into place as {hero.id}'s bright light settled over it."
            )


def tell_story(place: Place, task: Task, gear: Gear, hero_name: str, helper_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", label=helper_name))
    job = world.add(Entity(
        id="job",
        type="task",
        label="the job",
        phrase="the city job",
        owner=helper.id,
        caretaker=helper.id,
        meters={"done": 0.0, "tangled": 0.0},
        memes={"worry": 1.0},
    ))
    whirly = world.add(Entity(
        id="whirly",
        type="machine",
        label="the whirly machine",
        phrase="the whirly machine",
        meters={"spin": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, job=job, whirly=whirly, task=task, gear=gear)

    world.say(
        f"{hero.id} was a young superhero with a radiant glow who liked to help when a job got too hard."
    )
    world.say(
        f"That day, {helper.id} called for help because {place.label} had a job to finish before dusk."
    )
    world.say(
        f"The job was supposed to be simple, but the whirly machine kept spinning the pieces loose."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {task.verb}, and {hero.pronoun('possessive')} chest felt warm with bright power."
    )
    world.say(_inner_monologue(hero, task, "stuck"))
    world.say(
        f"{hero.id} tried to use the light to {task.verb}, but the whirly machine tugged the work sideways again."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    job.meters["tangled"] = job.meters.get("tangled", 0.0) + 1.0

    world.para()
    world.say(
        f"{helper.id} pointed to a narrow gap in the machine and said that a careful plan would work better than speed."
    )
    world.say(
        f"{hero.id} listened, took a breath, and put on {gear.label}."
    )
    world.say(
        f"Then {hero.id} used {gear.prep}."
    )
    world.say(
        f"{hero.id} thought, \"That is my job now: not just to shine, but to aim the shine.\""
    )

    if not reasonableness_gate(place, task, gear):
        raise StoryError(explain_rejection(place, task, gear))

    do_task(world, hero, task, narrate=True)
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0

    world.para()
    world.say(
        f"At last, the whirly machine slowed down, the job was finished, and {helper.id} cheered."
    )
    world.say(
        f"{hero.id} smiled at the clean result and thought, \"A radiant hero can be gentle too.\""
    )
    world.say(
        f"The evening light glowed on {place.label}, and the job stayed done."
    )
    world.facts.update(
        resolved=True,
        done=job.meters["done"] >= THRESHOLD,
        tangled=job.meters["tangled"] >= THRESHOLD,
    )
    return world


PLACES = {
    "plaza": Place(id="plaza", label="the plaza", indoors=False, acts={"whirly"}),
    "tower": Place(id="tower", label="the clock tower roof", indoors=False, acts={"whirly"}),
    "workshop": Place(id="workshop", label="the workshop", indoors=True, acts={"whirly"}),
}

TASKS = {
    "whirly": Task(
        id="whirly",
        verb="fix the whirly machine",
        gerund="fixing the whirly machine",
        need="careful light",
        obstacle="spin",
        zone="machine",
        keyword="whirly",
        tags={"whirly", "machine", "job"},
    ),
}

GEAR = {
    "visor": Gear(
        id="visor",
        label="a bright visor",
        helps={"whirly"},
        covers={"machine"},
        prep="the bright visor over the spinning gears",
        tail="the visor kept the glare steady",
    ),
}

HERO_NAMES = ["Nova", "Mira", "Iris", "Zara", "Luna"]
HELPER_NAMES = ["Captain Holt", "Aunt Bea", "Officer Lane", "Mr. Finch"]


@dataclass
class StoryParams:
    place: str
    task: str
    gear: str
    hero: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world with radiant light and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for g in GEAR:
                if reasonableness_gate(PLACES[p], TASKS[t], GEAR[g]):
                    combos.append((p, t, g))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, gear = rng.choice(combos)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, task=task, gear=gear, hero=hero, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    return [
        'Write a short superhero story for young children about a radiant hero and a whirly machine.',
        f"Tell a story where {hero.id} uses {task.keyword} power to solve a job that keeps spinning apart.",
        f"Write a gentle superhero story with inner monologue, a job to finish, and a bright plan that works.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    job = f["job"]
    task = f["task"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, who had a radiant glow and wanted to help with the job.",
        ),
        QAItem(
            question=f"What was the job that needed doing?",
            answer=f"The job was {task.gerund}, because the whirly machine kept making it hard to finish.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} used {f['gear'].label} and careful thinking to steady the whirly machine and finish the job.",
        ),
        QAItem(
            question=f"What did {hero.id} think to {hero.pronoun('subject')}self before the fix?",
            answer=f"{hero.id} thought that shining was not enough; the light had to be aimed carefully to help the job stay put.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does radiant mean?",
            answer="Radiant means shining brightly with light or warmth.",
        ),
        QAItem(
            question="What is a job?",
            answer="A job is a task or piece of work that needs to be finished.",
        ),
        QAItem(
            question="What does whirly mean?",
            answer="Whirly means spinning around quickly, often in a twisting way.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_valid(P,T,G) :- place(P), task(T), gear(G), acts(P,T), helps(G,T), covers(G,machine).
show_valid(P,T,G) :- task_valid(P,T,G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.acts):
            lines.append(asp.fact("acts", pid, a))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for t in sorted(g.helps):
            lines.append(asp.fact("helps", gid, t))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show show_valid/3."))
    return sorted(set(asp.atoms(model, "show_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        PLACES[params.place],
        TASKS[params.task],
        GEAR[params.gear],
        params.hero,
        params.helper,
    )
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
    StoryParams(place="plaza", task="whirly", gear="visor", hero="Nova", helper="Captain Holt"),
    StoryParams(place="tower", task="whirly", gear="visor", hero="Mira", helper="Aunt Bea"),
    StoryParams(place="workshop", task="whirly", gear="visor", hero="Iris", helper="Mr. Finch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show show_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
