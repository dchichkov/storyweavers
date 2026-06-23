#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/chop_manage_success_humor_bad_ending_animal.py
=====================================================================================================

A standalone storyworld for a tiny animal tale about a shared task, a funny
attempt, and a bad ending that still feels complete.

Premise:
- Forest animals are trying to manage a small job together.
- Someone thinks chopping something will make success easier.
- The story includes humor, a plan that works in the moment, and then a bad
  ending image proving what went wrong.

The world is intentionally small:
- typed entities with meters and memes
- a forward causal rule engine
- a reasonableness gate and inline ASP twin
- three Q&A sets grounded in world state
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
GOOD_HELP = {"knife", "axe", "saw"}
BAD_TWIST = {"slip", "snap", "spill", "crack"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    helper_to: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "badger", "mouse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"duck", "hedgehog", "squirrel", "beaver", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    noise: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    noun: str
    verb: str
    gerund: str
    trouble: str
    result: str
    laugh: str
    zone: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_success(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["chopped"] < THRESHOLD:
            continue
        sig = ("success", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["success"] += 1
        ent.memes["relief"] += 1
        out.append("__success__")
    return out


def _r_bad_twist(world: World) -> list[str]:
    out: list[str] = []
    for task in world.entities.values():
        if task.kind != "thing":
            continue
        if task.meters["broken"] < THRESHOLD and task.meters["messy"] < THRESHOLD:
            continue
        sig = ("bad", task.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.characters():
            ent.memes["worry"] += 1
        out.append("__bad__")
    return out


CAUSAL_RULES = [Rule("success", "social", _r_success), Rule("bad", "physical", _r_bad_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def challenge_at_risk(task: Task, tool: Tool) -> bool:
    return tool.safe and task.noun in {"log", "branch", "pumpkin", "rope"}


def best_fix(tool: Tool) -> bool:
    return tool.id in {"knife", "axe", "saw"}


def predict(world: World, actor: Entity, task: Task) -> dict:
    sim = world.copy()
    _do_chop(sim, sim.get(actor.id), task, narrate=False)
    return {
        "success": sim.get(actor.id).meters["chopped"] >= THRESHOLD,
        "mess": any(e.meters["messy"] >= THRESHOLD or e.meters["broken"] >= THRESHOLD for e in sim.entities.values()),
    }


def _do_chop(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    actor.meters["chopped"] += 1
    actor.memes["joy"] += 1
    task_entity = world.get("task")
    task_entity.meters["chopped"] += 1
    if task.id == "pumpkin":
        task_entity.meters["messy"] += 1
    if task.id == "rope":
        task_entity.meters["broken"] += 1
    propagate(world, narrate=narrate)


def setting_line(setting: Setting) -> str:
    return f"The {setting.place} was full of {setting.noise} and funny little plans."


def intro(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    world.say(
        f"{hero.id} was a {hero.type} who loved making a plan with {helper.id}. "
        f"They lived near {world.setting.place} and liked to laugh at their own ideas."
    )
    world.say(
        f"One day they needed to manage the {task.noun}. It looked simple, but it had a sneaky grin."
    )


def want(world: World, hero: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    hero.memes["want"] += 1
    helper.memes["want"] += 1
    world.say(
        f'"We can {task.verb} it," said {hero.id}. "{tool.phrase} will make success quick."'
    )
    world.say(
        f'{helper.id} blinked. "That sounds bold," {helper.pronoun()} said, "and maybe a little silly."'
    )


def warn(world: World, helper: Entity, hero: Entity, task: Task, tool: Tool, fix: Fix) -> None:
    pred = predict(world, hero, task)
    world.facts["predicted_mess"] = pred["mess"]
    world.facts["predicted_success"] = pred["success"]
    world.say(
        f'{helper.id} pointed at the {task.noun}. "If you use {tool.label}, the {task.trouble} could get worse," '
        f'{helper.pronoun()} said. "We should keep a {fix.label} nearby."'
    )


def chop_plan(world: World, hero: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    hero.memes["mischief"] += 1
    world.say(
        f"{hero.id} tried to manage the {task.noun} anyway. {tool.action.capitalize()}, and for a second it looked like success."
    )
    world.say(
        f"Then {task.laugh} -- the {task.noun} lurched, and the whole plan got wobbly."
    )


def finish_good(world: World, hero: Entity, helper: Entity, fix: Fix, task: Task) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} used {fix.phrase}, and the small mess stayed small. They managed the {task.noun} after all."
    )
    world.say(
        f"At the end, {hero.id} stood beside a neat pile and laughed at how close the little job had come to being a circus."
    )


def finish_bad(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    world.say(
        f"Oops -- the {task.noun} split open, crumbs and bits went everywhere, and both animals stared at the floor in silence."
    )
    world.say(
        f"By sunset, {hero.id} and {helper.id} had no tidy pile at all, only a sticky patch and a very silly-looking broom."
    )


SETTINGS = {
    "orchard": Setting(id="orchard", place="orchard", noise="buzzing bees", afford={"chop"}),
    "porch": Setting(id="porch", place="porch", noise="creaky boards", afford={"chop"}),
    "barnyard": Setting(id="barnyard", place="barnyard", noise="clucking chickens", afford={"chop"}),
    "riverbank": Setting(id="riverbank", place="riverbank", noise="shiny water", afford={"chop"}),
}

TASKS = {
    "log": Task(id="log", noun="log", verb="chop", gerund="chopping", trouble="splinters", result="split log", laugh="the log made a funny thunk", zone="ground", needs={"knife"}, tags={"wood", "chop"}),
    "pumpkin": Task(id="pumpkin", noun="pumpkin", verb="chop", gerund="chopping", trouble="seeds", result="pumpkin halves", laugh="the pumpkin wobbled like a jelly hat", zone="table", needs={"knife"}, tags={"food", "chop"}),
    "rope": Task(id="rope", noun="rope", verb="chop", gerund="chopping", trouble="frayed ends", result="snipped rope", laugh="the rope bounced like a noodle", zone="hook", needs={"saw"}, tags={"rope", "chop"}),
    "branch": Task(id="branch", noun="branch", verb="chop", gerund="chopping", trouble="twigs", result="small branches", laugh="the branch dropped a leaf on everyone's nose", zone="tree", needs={"axe"}, tags={"wood", "chop"}),
}

TOOLS = {
    "knife": Tool(id="knife", label="a little knife", phrase="a little knife", action="the knife flashed in the sun", safe=True, tags={"knife"}),
    "axe": Tool(id="axe", label="a tiny axe", phrase="a tiny axe", action="the tiny axe swung with a thump", safe=True, tags={"axe"}),
    "saw": Tool(id="saw", label="a hand saw", phrase="a hand saw", action="the saw sang back and forth", safe=True, tags={"saw"}),
}

FIXES = {
    "tray": Fix(id="tray", label="a tray", phrase="a tray", effect="catch the pieces", power=2, tags={"tray"}),
    "basket": Fix(id="basket", label="a basket", phrase="a basket", effect="hold the pieces", power=2, tags={"basket"}),
    "towel": Fix(id="towel", label="a towel", phrase="a towel", effect="mop the mess", power=1, tags={"towel"}),
}

GIRL_NAMES = ["Mina", "Luna", "Poppy", "Mabel", "Nina"]
BOY_NAMES = ["Otis", "Bram", "Finn", "Toby", "Wren"]
ANIMALS = ["fox", "rabbit", "beaver", "hedgehog", "duck", "mouse", "badger", "squirrel"]


@dataclass
class StoryParams:
    setting: str
    task: str
    tool: str
    fix: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TASKS:
            for tool in TOOLS:
                if challenge_at_risk(TASKS[t], TOOLS[tool]):
                    out.append((s, t, tool))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world about animal teamwork, chopping, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, tool = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_type = rng.choice(ANIMALS)
    helper_type = rng.choice([a for a in ANIMALS if a != hero_type])
    hero = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, task=task, tool=tool, fix=fix, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    fix = FIXES[params.fix]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    task_ent = world.add(Entity(id="task", kind="thing", type=task.id, label=task.noun, attrs={"task": task}))
    world.facts.update(hero=hero, helper=helper, task=task, tool=tool, fix=fix, setting=setting)
    hero.meters["chopped"] = 0
    helper.meters["chopped"] = 0
    task_ent.meters["chopped"] = 0
    task_ent.meters["messy"] = 0
    task_ent.meters["broken"] = 0
    intro(world, hero, helper, task)
    world.para()
    want(world, hero, helper, task, tool)
    warn(world, helper, hero, task, tool, fix)
    world.para()
    chop_plan(world, hero, helper, task, tool)
    _do_chop(world, hero, task)
    world.para()
    world.facts["bad"] = task_ent.meters["messy"] >= THRESHOLD or task_ent.meters["broken"] >= THRESHOLD
    if world.facts["bad"]:
        finish_bad(world, hero, helper, task)
    else:
        finish_good(world, hero, helper, fix, task)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    tool: Tool = f["tool"]
    fix: Fix = f["fix"]
    qa = [
        QAItem(
            question=f"What did {hero.id} and {helper.id} need to manage?",
            answer=f"They needed to manage the {task.noun}. It looked small, but it still needed a careful plan.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {task.noun}?",
            answer=f"{hero.id} wanted to chop it. {tool.label} made the idea look quick and funny.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about using {tool.label}?",
            answer=f"{helper.id} worried because the {task.trouble} could get worse. The job needed a safer setup before anyone could call it success.",
        ),
    ]
    if f["bad"]:
        qa.append(QAItem(
            question=f"What happened at the end when they tried to chop the {task.noun}?",
            answer=f"The {task.noun} split badly and made a bigger mess. They did not get a tidy success, only a sticky floor and a silly-looking cleanup.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did {fix.label} help them finish the job?",
            answer=f"{fix.label.capitalize()} helped keep the pieces together, so they could manage the {task.noun} and still end with success.",
        ))
    return qa


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task: Task = f["task"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a funny animal story that uses the words "chop", "manage", and "success".',
        f"Tell a small animal story where {hero.id} and {helper.id} try to manage a {task.noun} by chopping it, but the ending goes wrong in a silly way.",
        f"Write a humorous story about two animals and a {task.noun} that almost becomes success, but ends with a bad mess.",
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean to chop something?", "To chop something means to cut it with a sharp tool or quick hard swings."),
        QAItem("What does it mean to manage something?", "To manage something means to handle it or take care of it so it can get done."),
        QAItem("What is success?", "Success means a job works out the way you hoped."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="orchard", task="pumpkin", tool="knife", fix="basket", hero="Mina", hero_type="fox", helper="Otis", helper_type="rabbit"),
    StoryParams(setting="porch", task="log", tool="axe", fix="tray", hero="Luna", hero_type="squirrel", helper="Bram", helper_type="mouse"),
    StoryParams(setting="barnyard", task="branch", tool="saw", fix="towel", hero="Poppy", hero_type="beaver", helper="Finn", helper_type="duck"),
    StoryParams(setting="riverbank", task="rope", tool="knife", fix="basket", hero="Nina", hero_type="hedgehog", helper="Wren", helper_type="cat"),
]


ASP_RULES = r"""
task_success(H) :- hero(H), chopped(H).
bad_ending(T) :- task(T), messy(T).
valid(S, T, U) :- setting(S), task(T), tool(U), risk(T, U).
risk(T, U) :- task(T), tool(U), safe(U), needs(T, U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("needs", tid, next(iter(task.needs))))
    for uid, tool in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        if tool.safe:
            lines.append(asp.fact("safe", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP and Python valid_combos differ.")
            rc = 1
        else:
            print(f"OK: ASP and Python valid_combos match ({len(valid_combos())} combos).")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test produced a story.")
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def build_parser_and_resolve() -> None:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with chop/manage/success, humor, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, tool = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    hero_type = rng.choice(ANIMALS)
    helper_type = rng.choice([a for a in ANIMALS if a != hero_type])
    return StoryParams(setting=setting, task=task, tool=tool, fix=fix, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
