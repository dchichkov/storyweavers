#!/usr/bin/env python3
"""
storyworlds/worlds/dexterity_dialogue_nursery_rhyme.py
======================================================

A small story world for a nursery-rhyme-style dialogue tale about dexterity:
a child wants to do a tiny, tricky task, gets stuck, talks it through, and
finds a gentler way to finish.

The world model tracks:
- physical meters: neatness, progress, wobble, strain, confidence
- emotional memes: delight, frustration, pride, tenderness

The prose is child-facing and lightly rhyming in cadence, with dialogue woven
through the action.
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
    helper: Optional[str] = None
    tool_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["neatness", "progress", "wobble", "strain", "confidence"]:
            self.meters.setdefault(key, 0.0)
        for key in ["delight", "frustration", "pride", "tenderness", "patience"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def is_plural(self) -> bool:
        return False


@dataclass
class Setting:
    place: str
    mood: str
    light: str


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    trouble: str
    strain_word: str
    dexterity_need: float
    success_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    ease: float
    little: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    task = world.facts["task"]
    tool = world.facts.get("tool")
    if child.meters["wobble"] < THRESHOLD:
        return out
    sig = ("strain", task.id, tool.id if tool else "bare")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["strain"] += 1
    child.memes["frustration"] += 1
    out.append(f"{child.id} felt a pinch of strain and a bit of fuss.")
    return out


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    task = world.facts["task"]
    tool = world.facts.get("tool")
    ease = tool.meters["confidence_boost"] if tool else 0.0
    if child.memes["frustration"] >= THRESHOLD and ease >= 1.0 and child.meters["progress"] < 2:
        sig = ("progress", task.id, tool.id if tool else "none")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.meters["progress"] += 1
        child.meters["wobble"] = max(0.0, child.meters["wobble"] - 1)
        child.memes["pride"] += 1
        out.append(f"The tiny task moved along once the right little help arrived.")
    return out


CAUSAL_RULES = [_r_strain, _r_progress]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def child_name_phrase(name: str, kind: str) -> str:
    return f"little {name} the {kind}"


def setup_line(setting: Setting) -> str:
    return f"In {setting.place}, where the light was soft and fair, the day felt calm as a nursery rhyme air."


def task_line(task: Task) -> str:
    return f"There was a tiny task to {task.verb}, a nimble little job for careful fingers to share."


def tool_line(tool: Tool) -> str:
    return f"The help came in a small, neat sort of way: {tool.phrase} to make the fingers happy and spry."


def predict(world: World, child: Entity, task: Task, tool: Optional[Tool]) -> dict:
    sim = world.copy()
    sim.get(child.id).meters["wobble"] += 1
    if tool:
        sim.get(child.id).meters["confidence"] += tool.ease
    propagate(sim, narrate=False)
    return {
        "struggled": sim.get(child.id).meters["strain"] >= THRESHOLD,
        "worked": sim.get(child.id).meters["progress"] >= 1,
    }


def tell(setting: Setting, task: Task, tool: Tool, child_name: str, child_type: str, helper_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    tiny_tool = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=child.id,
        tool_for=task.id,
    ))
    tiny_tool.meters["confidence_boost"] = tool.ease

    child.memes["delight"] += 1
    child.meters["confidence"] += 0.2
    world.say(setup_line(setting))
    world.say(f"{child.id} was a {child_name_phrase(child_name, child_type)} with a bright eye for little things.")
    world.say(task_line(task))
    world.say(f"{child.id} loved the {task.verb} of it all, and hummed, \"I can do it, I can!\"")

    world.para()
    world.say(f"Then {child.id} tried to {task.verb}, but the task was {task.trouble}.")
    world.say(f"\"Oh dear,\" said {helper.label}, \"that takes steady dexterity and a calm, small hand.\"")
    child.meters["wobble"] += 1
    child.memes["frustration"] += 1
    predict(world, child, task, tiny_tool)
    propagate(world, narrate=True)

    world.para()
    world.say(f"\"Can you help me?\" said {child.id}.")
    world.say(f"\"Yes,\" said {helper.label}, \"let us use {tool.phrase}.\"")
    world.say(tool_line(tool))
    child.memes["tenderness"] += 1
    child.memes["patience"] += 1
    child.meters["confidence"] += tool.ease
    child.meters["wobble"] = max(0.0, child.meters["wobble"] - 1)
    child.meters["progress"] += 1
    child.memes["pride"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"At last {child.id} could {task.verb}, and {task.success_image}.")
    world.say(f"\"Look at me now!\" said {child.id}. \"My fingers learned their little dance.\"")
    world.say(f"\"Indeed,\" said {helper.label}, \"dexterity grows when we take it slow.\"")

    world.facts.update(
        child=child,
        helper=helper,
        tool=tiny_tool,
        task=task,
        setting=setting,
        success=child.meters["progress"] >= 1,
    )
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", mood="gentle", light="gold"),
    "workroom": Setting(place="a cozy workroom", mood="busy", light="warm"),
    "windowseat": Setting(place="a window seat", mood="quiet", light="silver"),
}

TASKS = {
    "buttons": Task(
        id="buttons",
        verb="button the tiny coat",
        gerund="buttoning tiny buttons",
        trouble="full of wee, slippery buttons",
        strain_word="button strain",
        dexterity_need=1.0,
        success_image="the coat sat neat and snug",
        tags={"buttons", "clothing", "dexterity"},
    ),
    "laces": Task(
        id="laces",
        verb="tie the shoe laces",
        gerund="tying shoe laces",
        trouble="all twisty and thin as grass",
        strain_word="lace strain",
        dexterity_need=1.2,
        success_image="the bows made two tidy butterfly wings",
        tags={"laces", "shoes", "dexterity"},
    ),
    "beads": Task(
        id="beads",
        verb="thread the beads",
        gerund="threading bright beads",
        trouble="so tiny they wanted to roll and roam",
        strain_word="bead strain",
        dexterity_need=0.9,
        success_image="the beads made a cheerful rainbow string",
        tags={"beads", "craft", "dexterity"},
    ),
    "spoons": Task(
        id="spoons",
        verb="stack the tiny spoons",
        gerund="stacking spoons so high",
        trouble="wobbly as a sleepy tower",
        strain_word="stack strain",
        dexterity_need=1.1,
        success_image="the spoons stood like a silver little hill",
        tags={"stacking", "balance", "dexterity"},
    ),
}

TOOLS = {
    "bigbutton": Tool(
        id="bigbutton",
        label="a button board",
        phrase="a button board with larger buttons",
        helps={"buttons"},
        ease=1.2,
        little="big enough to guide small fingers",
        tags={"buttons", "dexterity"},
    ),
    "lacecard": Tool(
        id="lacecard",
        label="a lace card",
        phrase="a lace card with wide holes and a soft ribbon",
        helps={"laces"},
        ease=1.2,
        little="made for little hands to practice",
        tags={"laces", "dexterity"},
    ),
    "beadstick": Tool(
        id="beadstick",
        label="a bead stick",
        phrase="a bead stick with a gentle tip",
        helps={"beads"},
        ease=1.1,
        little="easy to hold and hard to drop",
        tags={"beads", "dexterity"},
    ),
    "spoontray": Tool(
        id="spoontray",
        label="a spoon tray",
        phrase="a shallow spoon tray with little grooves",
        helps={"spoons"},
        ease=1.0,
        little="steady for careful stacking",
        tags={"spoons", "dexterity"},
    ),
}

CURATED = [
    ("nursery", "buttons", "bigbutton", "Pip", "boy", "grandmother"),
    ("workroom", "laces", "lacecard", "Mina", "girl", "mother"),
    ("windowseat", "beads", "beadstick", "Toby", "boy", "mother"),
    ("nursery", "spoons", "spoontray", "Nell", "girl", "grandfather"),
]

BOY_NAMES = ["Pip", "Toby", "Jack", "Theo", "Finn", "Leo"]
GIRL_NAMES = ["Mina", "Nell", "Rose", "Lila", "June", "Ivy"]


@dataclass
class StoryParams:
    setting: str
    task: str
    tool: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for t in TASKS.values():
            for u in TOOLS.values():
                if t.id in u.helps and t.dexterity_need <= u.ease + 0.3:
                    combos.append((s, t.id, u.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme-style story world about dexterity and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "grandmother", "father", "grandfather"])
    ap.add_argument("--name")
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
        task = TASKS[args.task]
        tool = TOOLS[args.tool]
        if task.id not in tool.helps:
            raise StoryError("That tool does not help with that tiny task.")
        if task.dexterity_need > tool.ease + 0.3:
            raise StoryError("That pairing is too clumsy to make a good story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "grandmother", "father", "grandfather"])
    return StoryParams(setting=setting, task=task_id, tool=tool_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], TOOLS[params.tool], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    tool = f["tool"]
    return [
        f'Write a short nursery-rhyme-style story about dexterity and dialogue that includes the word "dexterity".',
        f"Tell a gentle story where {child.id} wants to {task.verb} and learns with {tool.phrase}.",
        f"Write a simple tale with a small problem, spoken lines, and a tidy ending image about {task.success_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    task = f["task"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at first?",
            answer=f"{child.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"Who helped {child.id} with the tricky part?",
            answer=f"{helper.label} helped {child.id}.",
        ),
        QAItem(
            question=f"What did they use to make the task easier?",
            answer=f"They used {tool.phrase}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {task.success_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dexterity?",
            answer="Dexterity is skill in using your hands and fingers carefully and neatly.",
        ),
        QAItem(
            question="Why can tiny buttons be hard?",
            answer="Tiny buttons can be hard because they are small, slippery, and need careful fingers.",
        ),
        QAItem(
            question="Why do people practice small tasks?",
            answer="People practice small tasks so their hands learn to be steadier and more skillful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
task_ok(S,T,U) :- setting(S), task(T), tool(U), helps(U,T).
valid_story(S,T,U) :- task_ok(S,T,U).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
    for u in TOOLS.values():
        lines.append(asp.fact("tool", u.id))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", u.id, h))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(task: Task, tool: Tool) -> str:
    return f"(No story: {tool.label} does not fit {task.verb}; the pairing would not make a gentle dexterity tale.)"


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

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} compatible stories:")
        for s, t, u in items:
            print(f"  {s}  {t}  {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(setting=s, task=t, tool=u, name=n, gender=g, helper=h))
            for s, t, u, n, g, h in CURATED
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
