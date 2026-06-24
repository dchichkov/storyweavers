#!/usr/bin/env python3
"""
A heartwarming storyworld about a child being instructed through a small task,
making a few lively sound effects, and learning a gentle lesson with a clear
moral value at the end.

The story domain is intentionally small and classical:
- a child wants to complete a simple helping task
- an adult gives instructions
- the child gets excited, makes a little mess or mistake
- a helper offers a kinder, safer way
- the child learns a lesson and the ending proves the change

This script follows the Storyweavers contract and includes:
- typed entities with meters and memes
- a Python reasonableness gate
- an inline ASP twin
- registries, parameter resolution, generation, emission, and main()
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "order": 0.0, "done": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    instruction: str
    sound: str
    result: str
    mess: str
    fix: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    indoor: bool = True


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    finish: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"bake", "stir"}),
    "porch": Setting(place="the porch", indoor=False, affords={"plant", "windchime"}),
    "workbench": Setting(place="the little workbench", indoor=True, affords={"build", "fix"}),
}

TASKS = {
    "bake": Task(
        id="bake",
        verb="bake muffins",
        gerund="baking muffins",
        instruction="measure the flour, stir slowly, and pour the batter into the cups",
        sound="plop",
        result="soft, sweet muffins",
        mess="messy",
        fix="more careful steps",
        keyword="muffins",
        tags={"food", "warm", "mix"},
    ),
    "plant": Task(
        id="plant",
        verb="plant the seeds",
        gerund="planting seeds",
        instruction="poke a tiny hole, tuck in the seeds, and pat the soil flat",
        sound="pat-pat",
        result="little sprouts",
        mess="crumbly",
        fix="gentle hands",
        keyword="seeds",
        tags={"garden", "grow", "soil"},
    ),
    "build": Task(
        id="build",
        verb="build a bird feeder",
        gerund="building a bird feeder",
        instruction="fit the pieces together, tie the string, and check the roof",
        sound="tap-tap",
        result="a cozy feeder for birds",
        mess="scattered",
        fix="slow careful steps",
        keyword="bird feeder",
        tags={"wood", "helping", "birds"},
    ),
    "windchime": Task(
        id="windchime",
        verb="make a wind chime",
        gerund="making a wind chime",
        instruction="thread the beads, hang the pieces, and tie the last knot",
        sound="clink",
        result="a bright chime that sang in the breeze",
        mess="tangled",
        fix="one piece at a time",
        keyword="wind chime",
        tags={"music", "gift", "breeze"},
    ),
}

TOOLS = {
    "bowl": Tool(id="bowl", label="a mixing bowl", helps={"bake"}, prep="set out a mixing bowl", finish="brought the muffins to the table"),
    "spoon": Tool(id="spoon", label="a wooden spoon", helps={"bake"}, prep="picked up a wooden spoon", finish="stirred until the batter looked smooth"),
    "trowel": Tool(id="trowel", label="a little trowel", helps={"plant"}, prep="took a little trowel", finish="covered the seeds with soft soil"),
    "wateringcan": Tool(id="wateringcan", label="a small watering can", helps={"plant"}, prep="filled a small watering can", finish="gave the seeds a drink"),
    "hammer": Tool(id="hammer", label="a small hammer", helps={"build"}, prep="found a small hammer", finish="made the nails sit neatly"),
    "string": Tool(id="string", label="a spool of string", helps={"windchime"}, prep="got a spool of string", finish="made the chime hang straight"),
}

HELPERS = ["mother", "father", "grandma", "grandpa"]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Noah"]
TRAITS = ["curious", "gentle", "bright", "playful", "sweet", "eager"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for tool_id, tool in TOOLS.items():
                if task_id in tool.helps:
                    combos.append((place, task_id, tool_id))
    return combos


def prize_at_risk(task: Task, tool: Tool) -> bool:
    return task.id in tool.helps


def select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS.values():
        if task.id in tool.helps:
            return tool
    return None


def explain_rejection(task: Task, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit the task of {task.gerund}. "
        f"The helper needs a tool that honestly supports the steps, so this pair "
        f"is not a good story shape.)"
    )


@dataclass
class Rule:
    name: str
    apply: callable


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.memes.get("excited", 0.0) < THRESHOLD:
        return out
    sig = ("noise", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["mess"] += 1
    out.append(f"{child.pronoun().capitalize()} made a noisy {world.facts['task'].sound} and got a little messy.")
    return out


def _r_order(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.meters["mess"] < THRESHOLD:
        return out
    sig = ("order", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("That was a small sign to slow down and listen.")
    return out


def _r_learn(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    helper = world.entities.get("Helper")
    if not child or not helper:
        return out
    if child.memes.get("guided", 0.0) < THRESHOLD:
        return out
    sig = ("learn", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["lesson"] += 1
    child.memes["pride"] += 1
    out.append("The child learned that listening carefully can make a task feel easy and kind.")
    return out


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("order", _r_order), Rule("learn", _r_learn)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_result(world: World, child: Entity, task: Task) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["excited"] += 1
    sim.get(child.id).meters["mess"] += 1
    return {"messy": sim.get(child.id).meters["mess"] >= THRESHOLD}


def tell(setting: Setting, task: Task, tool_def: Tool, name: str, gender: str, helper_kind: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={"mess": 0.0, "order": 0.0, "done": 0.0}, memes={"joy": 0.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0, "excited": 0.0, "guided": 0.0}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label=helper_kind))
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label, owner=child.id, caretaker=helper.id, plural=tool_def.plural))
    world.facts.update(child=child, helper=helper, task=task, tool=tool, tool_def=tool_def)
    child.memes["joy"] += 1
    world.say(f"{child.id} was a little {gender} who loved helping in {setting.place}.")
    world.say(f"One day, {child.id}'s {helper_kind} gave a gentle instruct: '{task.instruction}.'")
    world.say(f"{child.id} listened, smiled, and wanted to {task.verb}.")
    world.para()
    world.say(f"At the {setting.place}, the room felt calm and ready.")
    world.say(f"{tool_def.prep.capitalize()}, and {child.id} reached for the first step.")
    world.say(f"{task.sound.capitalize()}! {child.id} moved fast, and a tiny bit of {task.mess} happened.")
    propagate(world, narrate=True)
    world.para()
    child.memes["guided"] += 1
    world.say(f"{helper_kind.capitalize()} came closer and showed {child.id} a kinder way: {task.fix}.")
    world.say(f"With help, {child.id} tried again, one careful step at a time.")
    child.meters["done"] += 1
    child.meters["mess"] = 0.0
    world.say(f"At last, {tool_def.finish}, and the work was finished.")
    world.say(f"{child.id} looked at the {task.keyword} result with a warm, proud smile.")
    child.memes["joy"] += 1
    world.say(f"Lesson learned: {task.fix} can turn a mistake into a happy success.")
    world.say(f"Moral value: kind instructions and patient listening help everyone do their best.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    helper = f["helper"]
    child = f["child"]
    return [
        f'Write a heartwarming story for a young child that includes the word "instruct" and the sound "{task.sound}".',
        f"Tell a gentle story where {helper.type} instructs {child.id} to {task.verb}, and the child learns a lesson.",
        f"Write a short story with a clear moral value about listening carefully while {task.gerund}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, task, tool = f["child"], f["helper"], f["task"], f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, who wanted to help by {task.gerund} with {tool.label}.",
        ),
        QAItem(
            question=f"What did {helper.type} tell {child.id} to do?",
            answer=f"{helper.type.capitalize()} told {child.id} to {task.instruction}.",
        ),
        QAItem(
            question=f"What sound did the story mention when {child.id} started working?",
            answer=f"The story said {task.sound}! when {child.id} began the task.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn at the end?",
            answer=f"{child.id} learned that listening carefully and taking one step at a time makes a job turn out well.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "food": [("Why do people measure ingredients?", "People measure ingredients so food turns out the right size and taste.")],
    "warm": [("Why can warm food feel comforting?", "Warm food can feel comforting because it is cozy and gentle to eat.")],
    "garden": [("Why do seeds need care?", "Seeds need water, soil, and patience to grow into plants.")],
    "wood": [("What is wood?", "Wood is a strong material that comes from trees and is used to make things like tables and toys.")],
    "music": [("What makes a wind chime sound?", "A wind chime sounds when the breeze moves its hanging pieces together.")],
    "gift": [("Why do people give gifts?", "People give gifts to show love, thanks, and care.")],
    "helping": [("What does helping mean?", "Helping means doing something kind that makes another person's job easier.")],
    "birds": [("Why do birds like feeders?", "Birds like feeders because they can find food there more easily.")],
    "soil": [("What is soil?", "Soil is the dark ground that helps plants grow.")],
    "breeze": [("What is a breeze?", "A breeze is a light, gentle wind that moves leaves and hangs up chimes.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_mess(C) :- excited(C), task(T), task_sound(T,_), started(C,T).
needs_slow(C) :- child_mess(C).
learned(C) :- guided(C), needs_slow(C).
good_story(P, T, U) :- setting(P), task(T), tool(U), helps(U, T), place_task(P, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("place_task", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_sound", tid, t.sound))
        for tg in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tg))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("helps", uid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    mapped = set()
    for place, task, tool in clingo_set:
        mapped.add((place, task, tool))
    if mapped == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(mapped)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if mapped - python_set:
        print("  only in clingo:", sorted(mapped - python_set))
    if python_set - mapped:
        print("  only in python:", sorted(python_set - mapped))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming instruct storyworld with lesson learned, sound effects, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
        task, tool = TASKS[args.task], TOOLS[args.tool]
        if not prize_at_risk(task, tool):
            raise StoryError(explain_rejection(task, tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task_id, tool_id = rng.choice(sorted(combos))
    task = TASKS[task_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, task=task_id, tool=tool_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], TOOLS[params.tool], params.name, params.gender, params.helper)
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
    StoryParams(place="kitchen", task="bake", tool="bowl", name="Mia", gender="girl", helper="grandma"),
    StoryParams(place="porch", task="plant", tool="trowel", name="Leo", gender="boy", helper="mother"),
    StoryParams(place="workbench", task="build", tool="hammer", name="Nora", gender="girl", helper="father"),
    StoryParams(place="porch", task="windchime", tool="string", name="Ben", gender="boy", helper="grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
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
