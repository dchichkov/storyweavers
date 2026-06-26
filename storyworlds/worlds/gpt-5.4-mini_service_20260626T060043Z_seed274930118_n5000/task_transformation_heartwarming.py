#!/usr/bin/env python3
"""
A heartwarming storyworld where a child faces a big task, then transforms it
into small, kind steps and finishes feeling proud.
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

TASK_THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    worry: str
    done_image: str
    kind: str
    steps: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    effect: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_steps(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("task_focus", 0.0) < TASK_THRESHOLD:
            continue
        task = world.entities.get("task")
        if not task:
            continue
        sig = ("step", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        task.meters["steps_started"] = task.meters.get("steps_started", 0) + 1
        ent.memes["care"] = ent.memes.get("care", 0) + 1
        out.append(f"{ent.id} looked at the big task and took a deep breath.")
    return out


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    task = world.entities.get("task")
    tool = world.entities.get("tool")
    if not child or not task or not tool:
        return out
    if child.meters.get("task_focus", 0.0) < TASK_THRESHOLD:
        return out
    if tool.worn_by != child.id:
        return out
    if task.meters.get("progress", 0.0) >= task.meters.get("needed", 3):
        return out
    sig = ("progress", task.id, task.meters.get("progress", 0.0))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    task.meters["progress"] = task.meters.get("progress", 0.0) + 1
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    out.append(f"The little checklist helped {child.id} finish one small part at a time.")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    task = world.entities.get("task")
    if not child or not parent or not task:
        return out
    if task.meters.get("progress", 0.0) < task.meters.get("needed", 3):
        return out
    sig = ("finish", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    child.memes["worry"] = 0
    parent.memes["warmth"] = parent.memes.get("warmth", 0) + 1
    out.append(f"{child.id} finished the task and smiled at {parent.id}.")
    return out


CAUSAL_RULES = [_r_steps, _r_progress, _r_finish]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_kind", tid, t.kind))
        lines.append(asp.fact("steps_needed", tid, t.steps))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
    return "\n".join(lines)


ASP_RULES = r"""
task_ready(T) :- task(T), task_kind(T,K), helps(tool1,K).
valid_story(S, T) :- setting(S), affords(S, K), task_kind(T, K), task_ready(T).
#show valid_story/2.
"""


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"sort", "pack", "wash"}),
    "bedroom": Setting(place="the bedroom", affords={"tidy", "pack"}),
    "porch": Setting(place="the porch", affords={"water", "sort"}),
}

TASKS = {
    "tidy-toys": Task(
        id="tidy-toys",
        verb="tidy the toys",
        gerund="tidying the toys",
        worry="too big and messy",
        done_image="the toy bin looked neat again",
        kind="tidy",
        steps=3,
        tags={"tidy", "clean"},
    ),
    "sort-crayons": Task(
        id="sort-crayons",
        verb="sort the crayons",
        gerund="sorting the crayons",
        worry="like a rainbow pile that went everywhere",
        done_image="the crayons stood in bright little rows",
        kind="sort",
        steps=3,
        tags={"sort", "colors"},
    ),
    "water-plant": Task(
        id="water-plant",
        verb="water the plant",
        gerund="watering the plant",
        worry="because the little pot looked thirsty",
        done_image="the leaves had perked up and shone",
        kind="water",
        steps=2,
        tags={"water", "plants"},
    ),
    "pack-bag": Task(
        id="pack-bag",
        verb="pack the school bag",
        gerund="packing the school bag",
        worry="because the bag needed books, lunch, and a note",
        done_image="the bag sat full and ready by the door",
        kind="pack",
        steps=4,
        tags={"pack", "school"},
    ),
}

TOOLS = {
    "checklist": Tool(
        id="checklist",
        label="a little checklist",
        prep="turn the task into tiny checkboxes",
        effect="helped the child see one small job at a time",
        helps={"tidy", "sort", "water", "pack"},
    ),
    "basket": Tool(
        id="basket",
        label="a bright basket",
        prep="gather the pieces into one soft basket",
        effect="made the toys easier to carry",
        helps={"tidy", "sort"},
    ),
    "watering-can": Tool(
        id="watering-can",
        label="a small watering can",
        prep="pour a careful little stream",
        effect="gave the plant just enough water",
        helps={"water"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming task transformation storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    tasks = list(TASKS)
    if args.place and args.task:
        if TASKS[args.task].kind not in SETTINGS[args.place].affords:
            raise StoryError("That setting cannot host that task in a believable way.")
    valid = [t for t in tasks if not args.place or TASKS[t].kind in SETTINGS[args.place].affords]
    if not valid:
        raise StoryError("No valid task fits the chosen setting.")
    task = args.task or rng.choice(valid)
    place = args.place or rng.choice([p for p, s in SETTINGS.items() if TASKS[task].kind in s.affords])
    name = args.name or rng.choice(["Mia", "Leo", "Nora", "Ben", "Ava", "Theo"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, task=task, name=name, parent=parent)


def _select_tool(task: Task) -> Tool:
    for tool in TOOLS.values():
        if task.kind in tool.helps:
            return tool
    raise StoryError("No helpful tool exists for that task.")


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    task_cfg = TASKS[params.task]
    tool = _select_tool(task_cfg)
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Leo", "Ben", "Theo"} else "girl"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    task = world.add(Entity(id="task", type="task"))
    task.label = task_cfg.verb
    task.phrase = f"a big task to {task_cfg.verb}"
    task.meters["needed"] = task_cfg.steps
    task.meters["progress"] = 0
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label))
    tool_ent.worn_by = child.id

    child.meters["task_focus"] = 1
    child.memes["worry"] = 1
    world.say(f"{child.id} stood in {setting.place} with a big task that felt {task_cfg.worry}.")
    world.say(f"{parent.id} came close and said, \"Let's make it gentle and small.\"")
    world.para()
    world.say(f"{parent.id} showed {child.id} {tool.prep}, and {tool.effect}.")
    world.say(f"{child.id} liked the idea and held on to {tool.label}.")
    propagate(world, narrate=True)
    world.para()
    if task.meters["progress"] < task.meters["needed"]:
        # keep moving until done
        while task.meters["progress"] < task.meters["needed"]:
            child.meters["task_focus"] = 1
            propagate(world, narrate=True)
    world.say(f"In the end, {task_cfg.done_image}, and {child.id} felt proud enough to smile big.")
    world.say(f"{parent.id} gave a warm hug, and the room felt calm and kind.")
    world.facts = {"task": task_cfg, "tool": tool, "child": child, "parent": parent, "setting": setting}
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    child = f["child"]
    return [
        f'Write a heartwarming story for a young child about a big task that becomes easier step by step.',
        f"Tell a gentle story where {child.id} feels worried about {task.verb} but a parent helps transform it into small pieces.",
        f'Write a simple story that includes the word "task" and ends with pride, a hug, and a finished job.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task = f["task"]
    child = f["child"]
    parent = f["parent"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.id} need to do in {setting.place}?",
            answer=f"{child.id} needed to {task.verb}. It felt big at first, but it could be done one small step at a time.",
        ),
        QAItem(
            question=f"How did {parent.id} help {child.id} with the task?",
            answer=f"{parent.id} helped by making the job feel smaller and kinder. That turned the task into something {child.id} could handle with a calm heart.",
        ),
        QAItem(
            question=f"How did the story end after {child.id} finished the task?",
            answer=f"It ended with {task.done_image}, {child.id} feeling proud, and {parent.id} giving a warm hug.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a checklist for?",
            answer="A checklist helps you remember little steps in a job so a big task feels easier and less scary.",
        ),
        QAItem(
            question="Why can small steps help with a big job?",
            answer="Small steps help because you do not have to think about everything at once. You can finish one part, then the next part.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for p, s in SETTINGS.items():
        for t in TASKS.values():
            if t.kind in s.affords:
                python_set.add((p, t.id))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


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
    StoryParams(place="kitchen", task="sort-crayons", name="Mia", parent="mother"),
    StoryParams(place="bedroom", task="tidy-toys", name="Leo", parent="father"),
    StoryParams(place="porch", task="water-plant", name="Nora", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
