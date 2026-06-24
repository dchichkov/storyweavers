#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/eligible_teamwork_slice_of_life.py
===============================================================================================================

A small slice-of-life story world about being eligible to join a teamwork job,
making a little plan together, and ending with a cozy proof that the job got
done.

The seed word is "eligible". The world models a simple everyday place where a
child wants to help, an adult checks what is needed, and a team learns how to
work together well.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap(self, text: str) -> str:
        return text[:1].upper() + text[1:] if text else text


@dataclass
class Place:
    name: str
    indoor: bool = False
    work: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    noun: str
    result: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        clone.entities = {k: Entity(**{**v.__dict__}) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def enough_for_task(actor: Entity, task: Task) -> bool:
    return all(actor.meters.get(need, 0.0) >= THRESHOLD for need in task.needs)


def select_tool(task: Task, tool_id: str) -> Optional[Tool]:
    tool = TOOLS.get(tool_id)
    if not tool:
        return None
    if task.id in tool.helps:
        return tool
    return None


def predict_can_help(world: World, helper: Entity, task: Task, tool: Optional[Tool]) -> bool:
    sim = world.copy()
    sim_helper = sim.get(helper.id)
    sim_helper.meters["prepared"] = sim_helper.meters.get("prepared", 0.0)
    if tool:
        sim_helper.meters["prepared"] += 1
    return enough_for_task(sim_helper, task) or (tool is not None and task.id in tool.helps)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for t in sorted(p.work):
            lines.append(asp.fact("work_at", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for n in sorted(t.needs):
            lines.append(asp.fact("needs", tid, n))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
    for gid, genders in ELIGIBILITY.items():
        for g in sorted(genders):
            lines.append(asp.fact("eligible_for", g, gid))
    return "\n".join(lines)


ASP_RULES = r"""
eligible(A, T) :- has_need(A, T), needs(T, N), prepared(A, N).
can_help(A, T) :- eligible(A, T).
can_help(A, T) :- tool_for(T, U), holds_tool(A, U).
teamwork_story(P, T, G) :- place(P), task(T), eligible_for(G, T), can_help(helper(G), T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show eligible/2.\n#show can_help/2.\n"))
    return sorted(set(asp.atoms(model, "eligible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def reasonableness_gate(task: Task, tool: Optional[Tool], place: Place) -> bool:
    if task.id not in place.work:
        return False
    if tool is None:
        return False
    return task.id in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            for tool_id, tool in TOOLS.items():
                if task_id in place.work and task_id in tool.helps:
                    combos.append((place_id, task_id, tool_id))
    return combos


def explain_rejection(task: Task, tool: Optional[Tool], place: Place) -> str:
    if task.id not in place.work:
        return f"(No story: {place.name} does not have {task.verb} to do, so there is no teamwork job there.)"
    if tool is None:
        return f"(No story: the chosen tool does not help with {task.verb}, so the team cannot finish the job in a believable way.)"
    return f"(No story: that combination is not eligible for a clean teamwork story.)"


def explain_gender(task_id: str, gender: str) -> str:
    ok = " / ".join(sorted(ELIGIBILITY[task_id]))
    return f"(No story: this role is not usually eligible here; try --gender {ok}.)"


def introduce(world: World, hero: Entity, adult: Entity, task: Task) -> None:
    world.say(
        f"{hero.id} was a {hero.type} who liked helping with small jobs at {world.place.name}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to join the team and help with {task.gerund}."
    )


def set_scene(world: World, task: Task, hero: Entity, adult: Entity, tool: Tool) -> None:
    world.say(
        f"At {world.place.name}, {adult.label} was getting the group ready for {task.gerund}."
    )
    world.say(
        f"{hero.id} looked at {tool.label} and hoped {hero.pronoun('subject')} would be eligible to help."
    )


def check_eligibility(world: World, hero: Entity, task: Task, tool: Tool) -> bool:
    if not enough_for_task(hero, task):
        world.say(
            f"{hero.id} did not have enough practice yet, so {hero.pronoun('subject')} could not start alone."
        )
        return False
    world.say(
        f"{hero.id} had the right kind of practice and was eligible for the job."
    )
    return True


def offer_tool(world: World, adult: Entity, hero: Entity, task: Task, tool: Tool) -> bool:
    if not predict_can_help(world, hero, task, tool):
        return False
    hero.meters["prepared"] = hero.meters.get("prepared", 0.0) + 1
    world.say(
        f"{adult.label} handed over {tool.label} and said, \"With this, you can help safely.\""
    )
    return True


def teamwork_turn(world: World, hero: Entity, adult: Entity, task: Task, tool: Tool) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} took a careful breath, then worked with {adult.label} side by side."
    )
    world.say(
        f"One of them held the {tool.label}, and the other kept the pieces steady."
    )
    hero.meters["done"] = hero.meters.get("done", 0.0) + 1
    adult.meters["done"] = adult.meters.get("done", 0.0) + 1


def finish(world: World, hero: Entity, adult: Entity, task: Task, tool: Tool) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    adult.memes["warmth"] = adult.memes.get("warmth", 0.0) + 1
    world.say(
        f"By the end, {task.result}, and {hero.id} felt proud to have helped."
    )
    world.say(
        f"{adult.label} smiled at the neat little finish and said it had been a good team job."
    )


def tell(place: Place, task: Task, tool: Tool, hero_name: str, hero_type: str, adult_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, label="the grown-up"))
    helper = world.add(Entity(id=tool.id, type="tool", label=tool.label))
    hero.meters["practice"] = 1.0
    hero.meters["prepared"] = 1.0
    world.facts.update(hero=hero, adult=adult, task=task, tool=tool, place=place)
    introduce(world, hero, adult, task)
    world.para()
    set_scene(world, task, hero, adult, helper)
    if not check_eligibility(world, hero, task, tool):
        return world
    world.para()
    if offer_tool(world, adult, hero, task, tool):
        teamwork_turn(world, hero, adult, task, helper)
        finish(world, hero, adult, task, helper)
    return world


PLACES = {
    "kitchen": Place(name="the kitchen", indoor=True, work={"sort", "wash"}),
    "garden": Place(name="the garden", indoor=False, work={"water", "sort"}),
    "laundry": Place(name="the laundry room", indoor=True, work={"fold", "wash"}),
    "library": Place(name="the library", indoor=True, work={"sort", "stack"}),
}

TASKS = {
    "sort": Task(
        id="sort",
        verb="sort the supplies",
        gerund="sorting the supplies",
        noun="supplies",
        result="the supplies were all lined up by size and color",
        needs={"focus"},
        tags={"order", "teamwork"},
    ),
    "wash": Task(
        id="wash",
        verb="wash the berries",
        gerund="washing the berries",
        noun="berries",
        result="the berries were clean and ready for snack time",
        needs={"care"},
        tags={"food", "teamwork"},
    ),
    "water": Task(
        id="water",
        verb="water the plants",
        gerund="watering the plants",
        noun="plants",
        result="the plants looked bright and happy with full leaves",
        needs={"gentle"},
        tags={"garden", "teamwork"},
    ),
    "fold": Task(
        id="fold",
        verb="fold the towels",
        gerund="folding the towels",
        noun="towels",
        result="the towels sat in one tidy stack on the shelf",
        needs={"care"},
        tags={"home", "teamwork"},
    ),
    "stack": Task(
        id="stack",
        verb="stack the storybooks",
        gerund="stacking the storybooks",
        noun="storybooks",
        result="the storybooks made a neat row on the table",
        needs={"focus"},
        tags={"quiet", "teamwork"},
    ),
}

TOOLS = {
    "basket": Tool(id="basket", label="a basket", helps={"sort", "wash"}, prep="bring a basket", tail="carried the basket back"),
    "watering_can": Tool(id="watering_can", label="a watering can", helps={"water"}, prep="bring a watering can", tail="filled the watering can"),
    "folding_board": Tool(id="folding_board", label="a folding board", helps={"fold"}, prep="bring a folding board", tail="set the folding board down"),
    "book_cart": Tool(id="book_cart", label="a little book cart", helps={"stack"}, prep="roll over a little book cart", tail="rolled the book cart close"),
}

ELIGIBILITY = {
    "sort": {"girl", "boy"},
    "wash": {"girl", "boy"},
    "water": {"girl", "boy"},
    "fold": {"girl", "boy"},
    "stack": {"girl", "boy"},
}

GIRL_NAMES = ["Mia", "Ava", "Nora", "Lily", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Max", "Theo", "Sam"]
TRAITS = ["curious", "cheerful", "helpful", "patient", "quiet", "brave"]


@dataclass
class StoryState:
    world: World


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, tool = f["hero"], f["task"], f["tool"]
    return [
        f'Write a short slice-of-life story about an eligible helper and teamwork using the word "eligible".',
        f"Tell a gentle story where {hero.id} wants to help with {task.gerund} at {world.place.name} and gets a chance to work on the team.",
        f"Write a simple story in which a child becomes eligible to help, uses {tool.label}, and finishes a small everyday job."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, adult, task, tool = f["hero"], f["adult"], f["task"], f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} want to help with at {world.place.name}?",
            answer=f"{hero.id} wanted to help with {task.gerund}.",
        ),
        QAItem(
            question=f"Why was {hero.id} eligible to join the team?",
            answer=f"{hero.id} was eligible because {hero.pronoun('subject')} had the needed practice and the job matched what {hero.pronoun('subject')} could do with help.",
        ),
        QAItem(
            question=f"What tool did {adult.label} give {hero.id}?",
            answer=f"{adult.label} gave {hero.id} {tool.label} so they could work together safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {task.result}, and {hero.id} felt proud to have helped with the team job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does eligible mean?",
            answer="Eligible means allowed to do something because you meet the needed rules or are a good fit.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help one another and share the work so a job gets done together.",
        ),
        QAItem(
            question="What is a slice of life story?",
            answer="A slice of life story is a small, everyday story about ordinary things people do in a normal day.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", task="sort", tool="basket", name="Mia", gender="girl", adult="mother", trait="helpful"),
    StoryParams(place="garden", task="water", tool="watering_can", name="Leo", gender="boy", adult="father", trait="curious"),
    StoryParams(place="laundry", task="fold", tool="folding_board", name="Nora", gender="girl", adult="mother", trait="patient"),
    StoryParams(place="library", task="stack", tool="book_cart", name="Ben", gender="boy", adult="father", trait="quiet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: eligible teamwork and a small everyday job.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.task and args.tool:
        task, tool = TASKS[args.task], TOOLS[args.tool]
        place = PLACES[args.place] if args.place else None
        if place and not reasonableness_gate(task, tool, place):
            raise StoryError(explain_rejection(task, tool, place))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, task_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.task and gender not in ELIGIBILITY[args.task]:
        raise StoryError(explain_gender(args.task, gender))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_id, task=task_id, tool=tool_id, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], TOOLS[params.tool], params.name, params.gender, params.adult)
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
        print(asp_program("#show eligible/2.\n#show can_help/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible (place, task, tool) combos")
        for place_id, task_id, tool_id in valid_combos():
            print(f"  {place_id:10} {task_id:8} {tool_id:14}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.task} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
