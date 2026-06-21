#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/poll_efficient_repetition_quest_slice_of_life.py
================================================================================

A small slice-of-life story world about a child doing a little quest at home,
where repeated attempts at an ordinary task reveal a more efficient way to finish
the job. The required seed words are woven in naturally: a neighborhood poll,
an efficient plan, repetition as a story instrument, and a gentle quest-like
journey through daily life.

The world keeps the classical Storyweavers shape:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- inline ASP twin rules and facts
- three separate Q&A sets grounded in world state
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
STEP_LIMIT = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    details: str


@dataclass
class Task:
    id: str
    noun: str
    verb: str
    repeated_verb: str
    quest_goal: str
    messy: bool = False
    asks_poll: bool = False
    makes_tired: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    efficient_for: str
    boost: int
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Outcome:
    id: str
    text: str
    repeat_text: str
    done_text: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["steps"] < STEP_LIMIT:
            continue
        sig = ("tired", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tired"] += 1
        e.memes["impatient"] += 1
        out.append("")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    task = world.facts["task"]
    if child.meters["attempts"] < 2:
        return out
    sig = ("repeat", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["frustration"] += 1
    out.append("")
    return out


CAUSAL_RULES = [
    Rule("tired", "social", _r_tired),
    Rule("repeat", "social", _r_repetition),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def task_is_reasonable(task: Task, setting: Setting) -> bool:
    return task.id in setting.id or task.asks_poll or task.makes_tired


def tool_is_reasonable(task: Task, tool: Tool) -> bool:
    return tool.efficient_for == task.id


def outcome_is_reasonable(task: Task, outcome: Outcome, tool: Tool) -> bool:
    return outcome.power + tool.boost >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if not task_is_reasonable(task, setting):
                continue
            for toolid, tool in TOOLS.items():
                if not tool_is_reasonable(task, tool):
                    continue
                for oid, outcome in OUTCOMES.items():
                    if outcome_is_reasonable(task, outcome, tool):
                        combos.append((sid, tid, toolid))
    return combos


def explain_rejection(task: Task, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} is not a good fit for {task.noun}. "
        f"The efficient tool must actually help with that task.)"
    )


def setup_world(setting: Setting, task: Task, tool: Tool, outcome: Outcome, *,
                child_name: str, child_gender: str, helper_name: str,
                helper_gender: str, parent_type: str) -> World:
    w = World()
    child = w.add(Entity(id=child_name, kind="character", type=child_gender, role="quester"))
    helper = w.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = w.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = w.add(Entity(id="room", label=setting.place, type="room"))
    poll = w.add(Entity(id="poll", label="the neighborhood poll", type="thing"))
    task_ent = w.add(Entity(id="task", label=task.noun, type="thing"))
    tool_ent = w.add(Entity(id="tool", label=tool.label, type="thing"))
    w.facts.update(setting=setting, task=task, tool=tool, outcome=outcome,
                   child=child, helper=helper, parent=parent, room=room, poll=poll,
                   task_ent=task_ent, tool_ent=tool_ent)
    child.meters["attempts"] = 0
    child.meters["steps"] = 0
    return w


def do_step(world: World, child: Entity, task: Task) -> None:
    child.meters["steps"] += 1
    child.meters["attempts"] += 1
    child.memes["hope"] += 1


def tell(setting: Setting, task: Task, tool: Tool, outcome: Outcome, *,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Theo", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = setup_world(setting, task, tool, outcome, child_name=child_name,
                        child_gender=child_gender, helper_name=helper_name,
                        helper_gender=helper_gender, parent_type=parent_type)
    child = world.get(child_name)
    helper = world.get(helper_name)
    parent = world.get("Parent")

    world.say(
        f"{child.id} was having a quiet day at {setting.place}. "
        f"{setting.details} {child.id} had one small quest to finish: {task.quest_goal}."
    )
    world.say(
        f"Nearby, a little neighborhood poll had asked everyone what would help most. "
        f"The answer was simple: do the job in an efficient way."
    )
    world.para()
    world.say(
        f"{child.id} tried to {task.verb}. Then {child.id} tried again. "
        f"After that, {child.id} tried one more time."
    )
    for _ in range(3):
        do_step(world, child, task)
        propagate(world, narrate=False)

    world.say(
        f"{helper.id} watched the repetition and pointed to {tool.label}. "
        f'"Use this," {helper.id} said. "It is the efficient way."'
    )
    child.memes["relief"] += 1
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} smiled and nodded. "
        f'The little quest was still ordinary, but now it felt lighter.'
    )
    world.say(
        f"{child.id} used {tool.phrase} and finished the task on the next try. "
        f"{task.done_text} {outcome.text}"
    )
    child.memes["pride"] += 1
    child.meters["done"] = 1
    world.facts["repeated"] = True
    world.facts["efficient"] = True
    world.facts["outcome_text"] = outcome.done_text
    return world


PROMPT_SETS = {
    "poll": [
        "Write a slice-of-life story about a child answering a neighborhood poll and learning to do one small job more efficiently.",
        "Tell a gentle story where repetition leads to a better plan after a poll asks what works well.",
        "Write a daily-life quest story that includes the word poll and ends with an efficient solution.",
    ],
    "efficient": [
        "Write a calm story about finding an efficient way to finish an everyday quest.",
        "Tell a small slice-of-life story where someone repeats a task, then chooses the efficient tool.",
        "Write a story that includes the word efficient and feels like a simple home-life adventure.",
    ],
}


STORY_QA_PROMPTS = [
    "What was the child trying to do?",
    "Why did the child repeat the task?",
    "How did the efficient tool help?",
    "How did the story end?",
]


WORLD_KNOWLEDGE = {
    "poll": [
        ("What is a poll?", "A poll is a simple way to ask people what they think or prefer."),
    ],
    "efficient": [
        ("What does efficient mean?", "Efficient means doing something in a way that saves time, effort, or both."),
    ],
    "repetition": [
        ("What is repetition?", "Repetition means doing the same thing again and again."),
    ],
    "quest": [
        ("What is a quest?", "A quest is a small journey or job where someone tries to reach a goal."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    task = world.facts["task"]
    return PROMPT_SETS["poll"][:2] + PROMPT_SETS["efficient"][:1] + [
        f"Write a slice-of-life quest about {world.get('child').id} trying to {task.verb} after a poll suggested an efficient way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        ("Who is the story about?", f"It is about {child.id}, who spends a quiet day at {setting.place}."),
        ("What small quest did the child have?", f"{child.id}'s quest was to {task.quest_goal}."),
        ("What happened before the efficient change?", f"{child.id} repeated the task three times and kept trying the same thing again."),
        ("What made the task easier?", f"{tool.label} made the job more efficient, so {child.id} could finish with less effort."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"poll", "efficient", "repetition", "quest"}
    out: list[tuple[str, str]] = []
    for key in ("poll", "efficient", "repetition", "quest"):
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", mood="cozy", details="The table was clear, and the morning light was soft."),
    "hall": Setting(id="hall", place="the hall", mood="quiet", details="The hall had a small bench and a row of shoes by the door."),
    "porch": Setting(id="porch", place="the porch", mood="gentle", details="The porch looked out at the street, where the day moved slowly."),
}

TASKS = {
    "dish_poll": Task(id="dish_poll", noun="the dish poll", verb="ask the neighbors about snacks", repeated_verb="ask again", quest_goal="collect the poll answers from the nearby homes", messy=False, asks_poll=True, tags={"poll", "quest"}),
    "toy_sort": Task(id="toy_sort", noun="the toy sort", verb="sort the toy bin", repeated_verb="sort again", quest_goal="put the toys back in the right basket", messy=False, makes_tired=True, tags={"repetition", "quest"}),
    "leaf_stack": Task(id="leaf_stack", noun="the leaf stack", verb="stack the leaves", repeated_verb="stack again", quest_goal="make the leaf pile neat for the yard", messy=True, tags={"repetition", "quest"}),
}

TOOLS = {
    "notebook": Tool(id="notebook", label="a small notebook", efficient_for="dish_poll", boost=1, phrase="a small notebook"),
    "basket": Tool(id="basket", label="a wide basket", efficient_for="toy_sort", boost=1, phrase="a wide basket"),
    "rake": Tool(id="rake", label="a light rake", efficient_for="leaf_stack", boost=1, phrase="a light rake"),
}

OUTCOMES = {
    "quiet": Outcome(id="quiet", text="The room stayed calm, and the job was done with a smile.", repeat_text="The same steps were repeated, but the new plan worked better.", done_text="Soon the little quest felt finished.", power=2),
    "simple": Outcome(id="simple", text="It was only a small change, but it made everything smoother.", repeat_text="Trying once more helped the child notice the better way.", done_text="That was enough to finish the quest.", power=2),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy"]
BOY_NAMES = ["Theo", "Owen", "Finn", "Leo"]


@dataclass
class StoryParams:
    setting: str
    task: str
    tool: str
    outcome: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


def valid_story(task: Task, tool: Tool) -> bool:
    return tool_is_reasonable(task, tool)


def explain_tool_rejection(task: Task, tool: Tool) -> str:
    return f"(No story: {tool.label} does not efficiently fit {task.noun}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: poll, repetition, quest, and an efficient slice-of-life turn.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    task = args.task or rng.choice(list(TASKS))
    tool = args.tool or rng.choice(list(TOOLS))
    outcome = args.outcome or rng.choice(list(OUTCOMES))
    if args.task and args.tool and not valid_story(TASKS[task], TOOLS[tool]):
        raise StoryError(explain_tool_rejection(TASKS[task], TOOLS[tool]))
    if args.child_gender and not args.child:
        args.child = rng.choice(GIRL_NAMES if args.child_gender == "girl" else BOY_NAMES)
    if args.helper_gender and not args.helper:
        args.helper = rng.choice(GIRL_NAMES if args.helper_gender == "girl" else BOY_NAMES)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, task=task, tool=tool, outcome=outcome,
                       child=child, child_gender=child_gender, helper=helper,
                       helper_gender=helper_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("task", TASKS), ("tool", TOOLS), ("outcome", OUTCOMES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"(Invalid {key}: {getattr(params, key)!r})")
    world = tell(SETTINGS[params.setting], TASKS[params.task], TOOLS[params.tool], OUTCOMES[params.outcome],
                 child_name=params.child, child_gender=params.child_gender, helper_name=params.helper,
                 helper_gender=params.helper_gender, parent_type=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(S, T, U) :- setting(S), task(T), tool(U), task_tool(T, U).
efficient(U) :- tool(U), task_tool(T, U).
repeated(T) :- task(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        if task.asks_poll:
            lines.append(asp.fact("asks_poll", tid))
        if task.makes_tired:
            lines.append(asp.fact("makes_tired", tid))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("task_tool", tool.efficient_for, tool_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: clingo gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, task=None, tool=None, outcome=None, child=None, child_gender=None, helper=None, helper_gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        cur = [
            StoryParams(setting="kitchen", task="dish_poll", tool="notebook", outcome="quiet", child="Mina", child_gender="girl", helper="Theo", helper_gender="boy", parent="mother"),
            StoryParams(setting="hall", task="toy_sort", tool="basket", outcome="simple", child="Theo", child_gender="boy", helper="Mina", helper_gender="girl", parent="father"),
        ]
        samples = [generate(p) for p in cur]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
