#!/usr/bin/env python3
"""
Standalone storyworld: elongate_teamwork_comedy

A small comedy world about a team trying to make something longer without
breaking it, while learning to coordinate. The seed word "elongate" is treated
as the central action: lengthening a shared object requires teamwork, timing,
and a silly compromise when the first plan goes wrong.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool
    surfaces: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    noun: str
    method: str
    risk: str
    target_zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    size: str
    role: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paras: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paras[-1].append(text)

    def para(self) -> None:
        if self.paras[-1]:
            self.paras.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paras if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name1: str
    name2: str
    seed: Optional[int] = None


PLACES = {
    "garage": Place("the garage", True, {"floor"}),
    "workshop": Place("the workshop", True, {"table"}),
    "yard": Place("the yard", False, {"ground"}),
}

TASKS = {
    "banner": Task(
        id="banner",
        verb="make a banner longer",
        noun="banner",
        method="stretching the banner",
        risk="rip",
        target_zone="table",
        tags={"cloth", "stretch"},
    ),
    "rope": Task(
        id="rope",
        verb="make the rope longer",
        noun="rope",
        method="pulling on the rope",
        risk="snap",
        target_zone="ground",
        tags={"rope", "stretch"},
    ),
    "slide": Task(
        id="slide",
        verb="make the slide longer",
        noun="slide",
        method="adding another piece",
        risk="wobble",
        target_zone="ground",
        tags={"wood", "build"},
    ),
}

TOOLS = {
    "hands": Tool("hands", "both hands", "use both hands", {"stretch", "build"}, "small", "team"),
    "clips": Tool("clips", "clothes clips", "clip the ends together", {"cloth"}, "tiny", "helper", plural=True),
    "planks": Tool("planks", "two short planks", "line up two short planks", {"build"}, "medium", "helper", plural=True),
}

NAMES = ["Mina", "Owen", "Pia", "Theo", "Ruth", "Ivy", "Leo", "Nia"]


class ReasonGate:
    @staticmethod
    def valid(place: str, task: str, tool: str) -> bool:
        return task in TASKS and tool in TOOLS and place in PLACES

    @staticmethod
    def compatible(place: str, task: str, tool: str) -> bool:
        t = TASKS[task]
        tl = TOOLS[tool]
        p = PLACES[place]
        if t.target_zone not in p.surfaces and p.indoor:
            return True
        return any(tag in tl.helps for tag in t.tags)

    @staticmethod
    def valid_combo(place: str, task: str, tool: str) -> bool:
        return ReasonGate.valid(place, task, tool) and ReasonGate.compatible(place, task, tool)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for t in TASKS:
            for u in TOOLS:
                if ReasonGate.valid_combo(p, t, u):
                    out.append((p, t, u))
    return out


def select_hero_names(rng: random.Random) -> tuple[str, str]:
    a, b = rng.sample(NAMES, 2)
    return a, b


def predict_problem(world: World, task: Task, tool: Tool) -> dict:
    if task.id == "banner" and "cloth" not in tool.helps:
        return {"worked": False, "mess": "the banner would wrinkle into a noodle"}
    if task.id == "rope" and tool.id == "hands":
        return {"worked": False, "mess": "the rope would stay short and grumpy"}
    return {"worked": True, "mess": ""}


def propagate(world: World) -> None:
    for ent in world.entities.values():
        if ent.meters.get("tension", 0) >= THRESHOLD and ent.meters.get("teamwork", 0) >= THRESHOLD:
            ent.memes["laugh"] = ent.memes.get("laugh", 0) + 1
            ent.meters["tension"] = 0.0


def tell_story(place: Place, task: Task, tool: Tool, name1: str, name2: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name1, kind="character", type="child"))
    pal = world.add(Entity(id=name2, kind="character", type="child"))
    shared = world.add(Entity(id="shared", type=task.noun, label=task.noun, phrase=f"a long {task.noun}", owner=name1))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=name2, plural=tool.plural))

    world.say(f"{name1} and {name2} were in {place.name}, staring at {shared.phrase} like it had told a joke they did not get.")
    world.say(f"They wanted to {task.verb}, because {task.method} sounded like a proper team mission.")
    hero.meters["desire"] = 1
    pal.meters["desire"] = 1

    world.para()
    world.say(f"At first, they tried to do it with {tool.label} and a very serious face.")
    pred = predict_problem(world, task, tool)
    if not pred["worked"]:
        hero.meters["tension"] = 1
        pal.meters["tension"] = 1
        world.say(f"It did not go well. {pred['mess'].capitalize()}.")
        if task.id == "banner":
            world.say(f"The banner flopped so hard it looked politely offended.")
        elif task.id == "rope":
            world.say(f"The rope wiggled and then refused to be longer by any meaningful amount.")
        else:
            world.say(f"The slide leaned a little, then made a face only a slide could make.")
        world.say(f"{name1} frowned. {name2} blinked. Then they both laughed, because the problem was too silly to stay mad at.")
    else:
        world.say(f"Luckily, {tool.label} actually helped, and the job started to look possible.")

    world.para()
    if task.id == "banner":
        world.say(f"{name2} clipped one end while {name1} held the other end straight.")
        world.say(f"Together they stretched the banner until it became long enough to wave in the air without tumbling into a twisty burrito.")
    elif task.id == "rope":
        world.say(f"{name1} held the rope steady while {name2} pulled in tiny, careful steps.")
        world.say(f"That teamwork made the rope grow longer without snapping, which felt almost magical and mostly just careful.")
    else:
        world.say(f"{name1} and {name2} lined up the pieces while {tool.label} kept everything from wobbling away.")
        world.say(f"With both of them helping, the slide became longer and sturdier, which made the whole yard look proud.")

    hero.meters["teamwork"] = 1
    pal.meters["teamwork"] = 1
    propagate(world)

    world.para()
    world.say(f"At the end, {shared.label} was longer, {name1} and {name2} were grinning, and even {tool.label} seemed pleased to have joined the crew.")
    world.facts.update(place=place, task=task, tool=tool, name1=name1, name2=name2, shared=shared, hero=hero, pal=pal)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    tool: Tool = f["tool"]
    place: Place = f["place"]
    return [
        f'Write a short comedy story for a young child about teamwork and the word "{task.id}".',
        f"Tell a funny story where two kids in {place.name} try to {task.verb} using {tool.label}.",
        f"Write a gentle, silly story about a team that learns how to elongate something safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    tool: Tool = f["tool"]
    name1: str = f["name1"]
    name2: str = f["name2"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What were {name1} and {name2} trying to do in {place.name}?",
            answer=f"They were trying to {task.verb}.",
        ),
        QAItem(
            question=f"Why did they use {tool.label}?",
            answer=f"They used {tool.label} because they needed help to {task.method} and make the job work as a team.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {task.noun} was longer, and the children were laughing because their teamwork worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something.",
        ),
        QAItem(
            question="Why is it funny when a plan goes wrong in a silly way?",
            answer="It can be funny because nobody is hurt, the mistake is small, and everyone can laugh and try again.",
        ),
        QAItem(
            question="What does it mean to elongate something?",
            answer="To elongate something means to make it longer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].indoor:
            lines.append(asp.fact("indoor", p))
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
        lines.append(asp.fact("risk", t.id, t.risk))
        lines.append(asp.fact("zone", t.id, t.target_zone))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", t.id, tag))
    for u in TOOLS.values():
        lines.append(asp.fact("tool", u.id))
        for tag in sorted(u.helps):
            lines.append(asp.fact("helps", u.id, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,U) :- place(P), task(T), tool(U), tag(T,Tag), helps(U,Tag).
valid(P,T,U) :- place(P), task(T), tool(U), indoor(P), risk(T,_), zone(T,_).
#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy teamwork storyworld about elongating things.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    if args.place or args.task or args.tool:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.task is None or c[1] == args.task)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, tool = rng.choice(sorted(combos))
    n1, n2 = args.name1, args.name2
    if not n1 or not n2:
        n1, n2 = select_hero_names(rng)
    if n1 == n2:
        raise StoryError("The two teammates need different names.")
    return StoryParams(place=place, task=task, tool=tool, name1=n1, name2=n2)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(PLACES[params.place], TASKS[params.task], TOOLS[params.tool], params.name1, params.name2)
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
    StoryParams(place="garage", task="banner", tool="clips", name1="Mina", name2="Owen"),
    StoryParams(place="workshop", task="slide", tool="planks", name1="Pia", name2="Theo"),
    StoryParams(place="yard", task="rope", tool="hands", name1="Leo", name2="Nia"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program())
        print("Models:", asp_valid_combos())
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
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
