#!/usr/bin/env python3
"""
Storyworld: palm transformation teamwork fable.

A small classical simulation in which a palm tree changes in a useful way only
because several helpers work together. The tone is fable-like: simple, concrete,
and slightly moral at the end.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"ant", "bee", "mouse", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hot desert edge"
    heat: str = "bright"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    struggle: str
    change: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    from_form: str
    to_form: str
    help_text: str
    result_text: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Team:
    id: str
    label: str
    members: int
    method: str
    payoff: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.steps: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.steps = list(self.steps)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "desert": Setting(place="the hot desert edge", heat="bright", affords={"shade", "cooling"}),
    "oasis": Setting(place="the oasis", heat="warm", affords={"shade", "cooling"}),
    "grove": Setting(place="the palm grove", heat="golden", affords={"shade", "cooling"}),
}

TASKS = {
    "bake": Task(
        id="bake",
        verb="make the fruit soft",
        gerund="softening the fruit",
        struggle="the fruit was too hard and dry",
        change="the fruit would become sweet and soft",
        keyword="fruit",
        tags={"palm", "fruit"},
    ),
    "shade": Task(
        id="shade",
        verb="turn the palm leaves into shade",
        gerund="making shade",
        struggle="the sun was too sharp",
        change="the ground would become cool and restful",
        keyword="shade",
        tags={"palm", "shade"},
    ),
    "rope": Task(
        id="rope",
        verb="weave a strong rope from the fronds",
        gerund="weaving fronds into rope",
        struggle="the fronds kept slipping apart",
        change="the rope would hold a basket steady",
        keyword="rope",
        tags={"palm", "rope"},
    ),
}

TRANSFORMS = {
    "fruit": Transformation(
        id="fruit",
        label="sweet fruit",
        from_form="hard green fruit",
        to_form="soft golden fruit",
        help_text="gently warm the fruit and wait for it to soften",
        result_text="the fruit had turned sweet and soft",
        requires={"warmth"},
        tags={"fruit", "palm"},
    ),
    "leafy_shade": Transformation(
        id="leafy_shade",
        label="cool shade",
        from_form="thin palm leaves",
        to_form="a cool umbrella of leaves",
        help_text="tie the leaves wide and let them spread",
        result_text="the palm cast a wide, cool shade",
        requires={"fronds"},
        tags={"shade", "palm"},
    ),
    "rope": Transformation(
        id="rope",
        label="rope",
        from_form="loose fronds",
        to_form="a strong woven rope",
        help_text="twist and braid the fronds together",
        result_text="the fronds became a rope that could hold weight",
        requires={"fronds"},
        tags={"rope", "palm"},
    ),
}

TEAMS = {
    "ants": Team(
        id="ants",
        label="a line of ants",
        members=6,
        method="they carried, tied, and pulled together",
        payoff="their tiny strength became one big strength",
        tags={"teamwork", "small"},
    ),
    "birds": Team(
        id="birds",
        label="three birds",
        members=3,
        method="they flew, pecked, and arranged the leaves",
        payoff="their quick wings made the work finish fast",
        tags={"teamwork", "light"},
    ),
    "mice": Team(
        id="mice",
        label="four mice",
        members=4,
        method="they held, nudged, and braided carefully",
        payoff="their careful paws kept the work neat",
        tags={"teamwork", "careful"},
    ),
}

HEROES = ["Mina", "Taro", "Ivo", "Nia", "Suri", "Kavi", "Lina", "Rafi"]
TRAITS = ["wise", "patient", "brave", "kind", "humble", "curious"]


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------
def task_needs_palm(task: Task, transform: Transformation) -> bool:
    return "palm" in task.tags and bool(task.keyword)


def compatible(task: Task, transform: Transformation, team: Team) -> bool:
    if not task_needs_palm(task, transform):
        return False
    if task.id == "bake":
        return transform.id == "fruit"
    if task.id == "shade":
        return transform.id == "leafy_shade"
    if task.id == "rope":
        return transform.id == "rope"
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for task in TASKS.values():
            for tr in TRANSFORMS.values():
                for team in TEAMS.values():
                    if place in SETTINGS and compatible(task, tr, team):
                        out.append((place, task.id, tr.id))
    # dedupe and keep only meaningful story combos
    return sorted(set(out))


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    transform: str
    team: str
    name: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, task: Task, palm: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a {hero.metas.get('trait', 'kind')} watcher "
        f"who loved the tall palm tree."
    )
    world.say(
        f"{hero.pronoun().capitalize()} noticed that the palm's {task.keyword} could become useful if "
        f"someone helped it change."
    )


def setup_entities(world: World, params: StoryParams) -> tuple[Entity, Entity, Transformation, Team, Task]:
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    hero.metas = {"trait": params.trait}
    palm = world.add(Entity(id="palm", kind="thing", type="palm", label="palm tree"))
    team = TEAMS[params.team]
    tr = TRANSFORMS[params.transform]
    task = TASKS[params.task]
    world.facts.update(hero=hero, palm=palm, team=team, transform=tr, task=task)
    return hero, palm, tr, team, task


def perform_task(world: World, hero: Entity, task: Task, team: Team, tr: Transformation, palm: Entity) -> None:
    world.say(
        f"One day, {hero.id} saw that {task.struggle}."
    )
    world.say(
        f"{hero.id} asked {team.label} to help, and {team.method}."
    )
    world.say(
        f"Together they worked on the palm so {tr.help_text}."
    )
    palm.meters["changed"] = palm.meters.get("changed", 0) + 1
    palm.memes["hope"] = palm.memes.get("hope", 0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    world.steps.append("teamwork_started")


def complete_transformation(world: World, hero: Entity, tr: Transformation, team: Team, palm: Entity) -> None:
    world.say(
        f"At last, the palm became different: {tr.result_text}."
    )
    world.say(
        f"{team.payoff}. {hero.id} smiled, because the little helpers had turned one hard thing into a better one."
    )
    palm.meters["transformed"] = palm.meters.get("transformed", 0) + 1
    palm.memes["gratitude"] = palm.memes.get("gratitude", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.steps.append("transformed")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero, palm, tr, team, task = setup_entities(world, params)
    world.para()
    world.say(f"Once in {world.setting.place}, {hero.id} watched a palm tree in the warm light.")
    world.say(f"{hero.id} was a {params.trait} child, and {hero.id} believed good work could be shared.")
    world.para()
    perform_task(world, hero, task, team, tr, palm)
    world.para()
    complete_transformation(world, hero, tr, team, palm)
    world.say("The lesson was simple: when many small hands work together, even a palm can change.")
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, tr, team = f["hero"], f["task"], f["transform"], f["team"]
    return [
        f'Write a short fable for children about a palm tree and {team.label} helping with {tr.label}.',
        f"Tell a gentle story where {hero.id} asks {team.label} to change a palm into something useful.",
        f'Write a simple moral tale that includes the word "palm" and ends with teamwork making a transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, task, tr, team = f["hero"], f["task"], f["transform"], f["team"]
    return [
        QAItem(
            question=f"What did {hero.id} want to change on the palm?",
            answer=f"{hero.id} wanted to help the palm become {tr.label} by working together with {team.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the palm?",
            answer=f"{team.label} helped {hero.id}, and they worked as a team.",
        ),
        QAItem(
            question=f"What made the transformation work?",
            answer=f"The transformation worked because everyone did a small part, and teamwork made the palm change.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a palm tree?",
            answer="A palm tree is a tall tree with long leaves that often grows in warm places.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do jobs together.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task_needs_palm(T) :- task(T), task_tag(T,palm).
compatible(P,T,R) :- place(P), task(T), transform(R), task_needs_palm(T), matches(T,R).
valid(P,T,R) :- place(P), compatible(P,T,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in task.tags:
            lines.append(asp.fact("task_tag", tid, tag))
    for rid, tr in TRANSFORMS.items():
        lines.append(asp.fact("transform", rid))
    for tid, tr in TEAMS.items():
        lines.append(asp.fact("team", tid))
    for task_id, tr_id in [("bake", "fruit"), ("shade", "leafy_shade"), ("rope", "rope")]:
        lines.append(asp.fact("matches", task_id, tr_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-world about a palm, transformation, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--team", choices=TEAMS)
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.transform:
        combos = [c for c in combos if c[2] == args.transform]
    if not combos:
        raise StoryError("No valid palm story fits those options.")
    place, task, transform = rng.choice(combos)
    team = args.team or rng.choice(list(TEAMS))
    if not compatible(TASKS[task], TRANSFORMS[transform], TEAMS[team]):
        raise StoryError("That team cannot reasonably complete this palm transformation.")
    name = args.name or rng.choice(HEROES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, transform=transform, team=team, name=name, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  steps: {world.steps}")
    return "\n".join(lines)


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
    StoryParams(place="desert", task="fruit", transform="fruit", team="ants", name="Mina", trait="wise"),
    StoryParams(place="oasis", task="shade", transform="leafy_shade", team="birds", name="Nia", trait="kind"),
    StoryParams(place="grove", task="rope", transform="rope", team="mice", name="Taro", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
