#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/synagogue_method_humor_transformation_teamwork_fable.py
==========================================================================================

A small fable-style story world about a synagogue, a practical method, a little
humor, and a teamwork-based transformation.

The seed words point to a gentle premise:
- a community gathers at a synagogue
- something needs to be done in a careful, useful way
- a character first tries a clumsy approach
- humor lightens the moment
- teamwork reveals a better method
- the ending shows a real transformation in the world

The domain is intentionally small and classical: one setting, a few characters,
one practical task, and a shared fix that changes the emotional state of the
group.
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
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "sparrow", "cat", "rabbit"}:
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
    place: str = "the synagogue courtyard"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    goal: str
    clumsy: str
    method: str
    mess: str
    humor: str
    transform: str
    keyword: str = "method"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    assists: set[str]
    prep: str
    outcome: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for tag in list(actor.meters.keys()):
            if actor.meters.get(tag, 0) < THRESHOLD:
                continue
            sig = ("mess", actor.id, tag)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["flustered"] = actor.memes.get("flustered", 0) + 1
            out.append(f"Their first attempt made the work a little messier.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("flustered", 0) < THRESHOLD:
            continue
        sig = ("laugh", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["humor"] = actor.memes.get("humor", 0) + 1
        out.append("The children laughed gently, and the worry softened.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    helpers = [e for e in world.characters() if e.memes.get("helping", 0) >= THRESHOLD]
    for actor in world.characters():
        if actor.memes.get("shared_effort", 0) < THRESHOLD:
            continue
        sig = ("teamwork", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["teamwork"] = actor.memes.get("teamwork", 0) + 1
        out.append("Everyone joined in, each doing a small part.")
    if helpers:
        world.facts["helpers"] = [h.id for h in helpers]
    return out


RULES = [
    Rule("mess", _r_mess),
    Rule("laugh", _r_laugh),
    Rule("teamwork", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            new = rule.apply(world)
            if new:
                changed = True
                out.extend(new)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters[task.id] = actor.meters.get(task.id, 0) + 1
    actor.memes["determination"] = actor.memes.get("determination", 0) + 1
    propagate(world, narrate=narrate)


def choose_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.assists:
            return tool
    return None


def predict(world: World, actor: Entity, task: Task) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    return {
        "flustered": any(e.memes.get("flustered", 0) >= THRESHOLD for e in sim.characters()),
        "teamwork": any(e.memes.get("teamwork", 0) >= THRESHOLD for e in sim.characters()),
    }


def tell(setting: Setting, task: Task, tool_cfg: Tool, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="mouse"))
    helper = world.add(Entity(id=helper_name, kind="character", type="sparrow"))
    keeper = world.add(Entity(id="keeper", kind="character", type="woman", label="the keeper"))
    item = world.add(Entity(id="lanterns", type="lanterns", plural=True, label="lanterns", caretaker=keeper.id))

    world.say(f"{hero.id} was a small mouse who liked useful tricks and careful days.")
    world.say(f"{hero.id} wanted to {task.goal}, and {helper.id} was happy to help.")
    world.say(f"Near the synagogue courtyard, {keeper.label} watched over the old {item.label}.")
    world.para()

    world.say(f"One day, {hero.id} tried to {task.clumsy}.")
    _do_task(world, hero, task, narrate=True)
    world.say(task.humor)
    hero.memes["flustered"] = hero.memes.get("flustered", 0) + 1
    propagate(world, narrate=True)

    world.para()
    tool = world.add(Entity(id=tool_cfg.id, type="tool", label=tool_cfg.label))
    world.say(f"Then {helper.id} pointed to {tool.label} and said, '{tool_cfg.prep}.'")
    hero.memes["shared_effort"] = hero.memes.get("shared_effort", 0) + 1
    helper.memes["helping"] = helper.memes.get("helping", 0) + 1
    world.say(f"{hero.id} listened, and together they used a better method.")
    world.say(f"They worked side by side until the {task.transform} was complete.")
    hero.memes["transformation"] = hero.memes.get("transformation", 0) + 1
    keeper.memes["relief"] = keeper.memes.get("relief", 0) + 1
    world.say(f"In the end, the synagogue courtyard looked {task.transform}, and everyone felt proud.")
    world.facts.update(hero=hero, helper=helper, keeper=keeper, task=task, tool=tool, setting=setting)
    return world


SETTINGS = {
    "synagogue": Setting(place="the synagogue courtyard", indoors=False, affords={"clean", "sort", "carry"}),
    "hall": Setting(place="the synagogue hall", indoors=True, affords={"clean", "sort", "carry"}),
}

TASKS = {
    "clean": Task(
        id="clean",
        goal="clean the benches",
        clumsy="push the dust with a scarf",
        method="use a soft brush in short strokes",
        mess="dusty",
        humor="A sneezy puff of dust made everyone giggle.",
        transform="bright and tidy",
        tags={"synagogue", "humor", "transformation", "teamwork"},
    ),
    "sort": Task(
        id="sort",
        goal="sort the prayer books",
        clumsy="pile the books in one wobbly heap",
        method="make neat stacks by size and color",
        mess="mixed-up",
        humor="The tallest stack leaned like a sleepy tower, and that looked funny.",
        transform="orderly and calm",
        tags={"synagogue", "humor", "transformation", "teamwork"},
    ),
    "carry": Task(
        id="carry",
        goal="carry the folded cloths",
        clumsy="drag the cloths in a snaking line",
        method="tie them into two balanced bundles",
        mess="tangled",
        humor="The cloths slid like a playful ribbon, which made the sparrow chirp.",
        transform="carefully arranged",
        tags={"synagogue", "humor", "transformation", "teamwork"},
    ),
}

TOOLS = [
    Tool(
        id="brush",
        label="a soft brush",
        assists={"clean"},
        prep="Let's use a soft brush and small circles",
        outcome="The dust was brushed away without fuss.",
    ),
    Tool(
        id="labels",
        label="little labels",
        assists={"sort"},
        prep="Let's sort them by size and color",
        outcome="The books found their places neatly.",
    ),
    Tool(
        id="cords",
        label="two cords",
        assists={"carry"},
        prep="Let's tie each bundle with a cord",
        outcome="The cloths stayed balanced and easy to carry.",
    ),
]

HERO_NAMES = ["Milo", "Tavi", "Nina", "Rafi", "Lena", "Suri"]
HELPER_NAMES = ["Pip", "Wren", "Ari", "Nori", "Bea", "Jax"]


@dataclass
class StoryParams:
    place: str
    task: str
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            if choose_tool(TASKS[task_id]):
                combos.append((place, task_id))
    return combos


def explain_rejection(task: Task) -> str:
    return f"(No story: there is no good tool for {task.goal}; the method must actually help.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable story world about a synagogue, a method, humor, transformation, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    if args.task and args.task not in TASKS:
        raise StoryError("Unknown task.")
    if args.task and not choose_tool(TASKS[args.task]):
        raise StoryError(explain_rejection(TASKS[args.task]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, task=task, hero=hero, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable about a synagogue, a useful method, and a team that learns together.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} solve a task at {f['setting'].place} with humor and teamwork.",
        f'Write a child-friendly fable that includes the word "method" and ends with a transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who learned a better method in the synagogue courtyard?",
            answer=f"{hero.id} learned a better method with help from {helper.id} at {setting.place}.",
        ),
        QAItem(
            question=f"What did {tool.label} help them do?",
            answer=f"It helped them {task.goal} in a careful, teamwork-filled way.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The {setting.place} became {task.transform}, and the work felt shared instead of clumsy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a synagogue?",
            answer="A synagogue is a place where Jewish people gather to pray, learn, and meet together.",
        ),
        QAItem(
            question="What is a method?",
            answer="A method is a way of doing something step by step so the job goes better.",
        ),
        QAItem(
            question="Why do teams work well?",
            answer="Teams work well because people can share jobs, ideas, and support each other.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can help because a kind joke can make people relax and keep trying.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state into another, like messy becoming neat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_combo(P,T) :- setting(P), affords(P,T), tool(T).
good_story(P,T) :- task_combo(P,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    tool_cfg = choose_tool(task)
    if tool_cfg is None:
        raise StoryError(explain_rejection(task))
    world = tell(setting, task, tool_cfg, params.hero, params.helper)
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
    StoryParams(place="synagogue", task="clean", hero="Milo", helper="Pip"),
    StoryParams(place="synagogue", task="sort", hero="Nina", helper="Wren"),
    StoryParams(place="hall", task="carry", hero="Tavi", helper="Ari"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show good_story/2."))
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
