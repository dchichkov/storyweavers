#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/microscopic_moral_value_lesson_learned_transformation_rhyming.py
==============================================================================================================

A tiny storyworld about a microscopic helper, a small mistake, and a gentle
transformation. The prose is written in a child-friendly rhyming style, with a
clear moral value and lesson learned.

Seed image:
- A microscopic seedling or speck-sized helper wants to do one important task.
- It rushes too fast, makes a tiny mess, then learns a kinder, safer way.
- In the end, it changes into something better.

This world keeps the simulation small on purpose:
- a single actor,
- a single task,
- one risky choice,
- one corrective lesson,
- one transformation at the end.

The story is driven by world state, not a frozen template: meter changes and
memetic changes influence what gets narrated.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clean": 0.0, "mess": 0.0, "grown": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "wisdom": 0.0, "kindness": 0.0}

    def pronoun(self) -> str:
        return "it"

    def poss(self) -> str:
        return "its"


@dataclass(frozen=True)
class Place:
    name: str
    affords: set[str]


@dataclass(frozen=True)
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    lesson: str
    moral: str
    rhyme_a: str
    rhyme_b: str
    transform_to: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Prize:
    label: str
    phrase: str
    region: str
    at_risk_when: set[str]


@dataclass(frozen=True)
class Aid:
    id: str
    label: str
    offer: str
    closing: str
    helps: set[str]
    covers: set[str]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = dict(self.facts)
        return w


def rhyme_end(word: str) -> str:
    return word


def join_two(a: str, b: str) -> str:
    return f"{a}, {b}"


PLACEMENTS = {
    "microscopic_garden": Place("the microscopic garden", {"sprout", "glitter", "splash"}),
    "microscopic_pond": Place("the microscopic pond", {"splash", "glitter"}),
    "microscopic_workbench": Place("the microscopic workbench", {"glitter", "sprout"}),
}

TASKS = {
    "sprout": Task(
        id="sprout",
        verb="help the tiny seed sprout",
        gerund="helping the tiny seed sprout",
        rush="rush to tug the sprout",
        mess="mud",
        lesson="slow and gentle hands do the best good",
        moral="kindness grows when you help, not hurry",
        rhyme_a="bright",
        rhyme_b="light",
        transform_to="a little green sprout helper",
        tags={"microscopic", "growth"},
    ),
    "glitter": Task(
        id="glitter",
        verb="polish the tiny lantern",
        gerund="polishing the tiny lantern",
        rush="dash to scrub too fast",
        mess="sparkle",
        lesson="careful steps keep bright things neat",
        moral="good work shines when done with care",
        rhyme_a="glow",
        rhyme_b="slow",
        transform_to="a shining lamp-sprite",
        tags={"microscopic", "care"},
    ),
    "splash": Task(
        id="splash",
        verb="carry a droplet to the fern",
        gerund="carrying a droplet to the fern",
        rush="race to pour it all at once",
        mess="wet",
        lesson="small drops, shared kindly, help things live",
        moral="sharing gently is a lovely choice",
        rhyme_a="near",
        rhyme_b="clear",
        transform_to="a dew-bright helper",
        tags={"microscopic", "water"},
    ),
}

PRIZES = {
    "leaf": Prize("leaf", "a tiny leaf", "leaf", {"sprout"}),
    "lamp": Prize("lamp", "a tiny lamp", "lamp", {"glitter"}),
    "fern": Prize("fern", "a little fern", "fern", {"splash"}),
}

AIDS = {
    "slow_breath": Aid(
        id="slow_breath",
        label="a slow breath",
        offer="take a slow breath and try again",
        closing="took a slow breath first",
        helps={"sprout", "glitter", "splash"},
        covers={"mess"},
    ),
    "tiny_gloves": Aid(
        id="tiny_gloves",
        label="tiny gloves",
        offer="wear tiny gloves to keep careful hands clean",
        closing="wore tiny gloves",
        helps={"sprout", "glitter"},
        covers={"mess"},
    ),
    "little_watering_jar": Aid(
        id="little_watering_jar",
        label="a little watering jar",
        offer="use a little watering jar instead of a big splash",
        closing="used a little watering jar",
        helps={"splash"},
        covers={"wet"},
    ),
}

NAMES = ["Milo", "Luna", "Pip", "Tia", "Nori", "Kiko"]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    seed: Optional[int] = None


def is_reasonable(task: Task, prize: Prize) -> bool:
    return task.id in prize.at_risk_when


def select_aid(task: Task, prize: Prize) -> Optional[Aid]:
    for aid in AIDS.values():
        if task.id in aid.helps:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACEMENTS.items():
        for task_id, task in TASKS.items():
            if task_id not in place.affords and place_id != "microscopic_workbench":
                continue
            for prize_id, prize in PRIZES.items():
                if is_reasonable(task, prize) and select_aid(task, prize):
                    out.append((place_id, task_id, prize_id))
    return out


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters["clean"] += 0.2
    actor.meters["mess"] += 1.0
    actor.memes["joy"] += 1.0
    if task.id == "sprout":
        actor.meters["grown"] += 1.0
    if narrate:
        world.say(f"{actor.id} started {task.gerund}, and the tiny world began to hum.")


def predict_consequence(world: World, actor: Entity, task: Task, prize: Prize) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    return {
        "messy": True,
        "prize_at_risk": task.id in prize.at_risk_when,
        "worry": sim.get(actor.id).memes["worry"],
    }


def tell(place: Place, task: Task, prize: Prize, name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="micro-helper"))
    prize_ent = world.add(Entity(id="prize", type=prize.label, label=prize.label, phrase=prize.phrase))
    world.facts.update(hero=hero, prize=prize_ent, task=task, place=place, aid=None)

    world.say(f"In {place.name}, {hero.id} was a microscopic little star.")
    world.say(
        f"{hero.id} loved {task.gerund}, and the day felt like a song so bright and light."
    )
    world.say(f"{hero.id} found {prize.phrase} and wanted to {task.verb} just right.")

    world.say(
        f"But {hero.id} got too quick and tried to {task.rush}, and that made a tiny mess take flight."
    )
    hero.memes["worry"] += 1.0
    predict = predict_consequence(world, hero, task, prize)
    if predict["prize_at_risk"]:
        world.say(
            f"The little mistake could trouble {prize.phrase}, and that did not feel kind or right."
        )

    aid = select_aid(task, prize)
    world.facts["aid"] = aid
    if aid is None:
        raise StoryError("No wise aid exists for this tiny tale.")

    world.say(
        f"Then {hero.id} paused and learned the lesson: {aid.offer}, and keep the pace polite."
    )
    hero.memes["wisdom"] += 1.0
    hero.memes["kindness"] += 1.0
    hero.memes["worry"] = 0.0
    _do_task(world, hero, task, narrate=False)

    world.say(
        f"{hero.id} {aid.closing}, and the work grew neat and neat in the gentle light."
    )
    world.say(
        f"In the end, {hero.id} became {task.transform_to}, and the moral was simple and bright: "
        f"{task.moral}."
    )
    hero.meters["grown"] += 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    prize: Prize = f["prize"]
    return [
        f"Write a microscopic rhyming story about {f['hero'].id} who wants to {task.verb}.",
        f"Tell a child-friendly moral value lesson learned story where a tiny helper learns not to {task.rush}.",
        f"Write a short transformation story about {prize.phrase} and a microscopic character in a gentle rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    task: Task = f["task"]
    prize: Prize = f["prize"]
    aid: Aid = f["aid"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the microscopic story?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What mistake did {hero.id} make when things got too fast?",
            answer=f"{hero.id} tried to {task.rush}, and that made a tiny mess.",
        ),
        QAItem(
            question=f"What lesson did the story teach?",
            answer=f"The lesson learned was that {task.lesson}.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end?",
            answer=f"{hero.id} transformed into {task.transform_to}.",
        ),
        QAItem(
            question=f"What helped {hero.id} finish the task more safely?",
            answer=f"{aid.label} helped because it let {hero.id} slow down and act carefully.",
        ),
        QAItem(
            question=f"What moral value did the story keep repeating?",
            answer=f"The moral value was kindness, care, and patience.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does microscopic mean?",
            answer="Microscopic means so small that you usually need a microscope to see it well.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is the helpful idea a character understands after making a mistake.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good choice like kindness, honesty, patience, or care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="microscopic_garden", task="sprout", prize="leaf", name="Milo"),
    StoryParams(place="microscopic_pond", task="splash", prize="fern", name="Luna"),
    StoryParams(place="microscopic_workbench", task="glitter", prize="lamp", name="Pip"),
]


ASP_RULES = r"""
task_at_risk(T, P) :- at_risk(T, P).
has_aid(T, P) :- task_at_risk(T, P), aid_for(T, P).

valid_story(Place, T, P) :- place_affords(Place, T), task_at_risk(T, P), has_aid(T, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACEMENTS.items():
        lines.append(asp.fact("place_affords", pid, next(iter(place.affords)) if place.affords else "none"))
        for t in sorted(place.affords):
            lines.append(asp.fact("place_affords", pid, t))
    for tid, task in TASKS.items():
        for tag in sorted(task.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for prid, prize in PRIZES.items():
        for t in sorted(prize.at_risk_when):
            lines.append(asp.fact("at_risk", t, prid))
    for aid in AIDS.values():
        for t in sorted(aid.helps):
            lines.append(asp.fact("aid_for", t, aid.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python for {len(py)} valid stories.")
        return 0
    print("Mismatch between ASP and Python:")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A microscopic rhyming moral storyworld.")
    ap.add_argument("--place", choices=PLACEMENTS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid microscopic story matches those options.")
    place, task, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, task=task, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACEMENTS[params.place], TASKS[params.task], PRIZES[params.prize], params.name)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.name}: {p.task} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
