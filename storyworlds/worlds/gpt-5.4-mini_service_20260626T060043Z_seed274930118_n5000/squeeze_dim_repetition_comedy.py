#!/usr/bin/env python3
"""
A tiny comedy storyworld about repetition, squeeze-dim places, and one stubborn
problem that gets solved by changing the approach instead of forcing the same
move twice.

The seed premise:
- A character wants to get or do something in a squeeze-dim space.
- Repetition makes the first attempt fail in a funny, escalating way.
- A helpful turn changes the method, and the ending proves the change worked.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    squeeze_dim: str
    affordance: str
    crowding: int


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    attempt: str
    outcome: str
    comedy: str
    repeated_sound: str
    requires: str
    keyword: str


@dataclass
class Fix:
    id: str
    label: str
    method: str
    helps: str
    result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hallway": Setting(place="the hallway", squeeze_dim="narrow", affordance="passing by", crowding=3),
    "closet": Setting(place="the closet", squeeze_dim="squeeze-dim", affordance="finding things", crowding=4),
    "bus": Setting(place="the bus aisle", squeeze_dim="tight", affordance="getting through", crowding=5),
    "shed": Setting(place="the garden shed", squeeze_dim="tiny", affordance="fetching tools", crowding=2),
}

TASKS = {
    "box": Task(
        id="box",
        verb="fit the big box through the opening",
        gerund="fitting the big box through the opening",
        attempt="push the box again",
        outcome="the box got stuck like a grumpy toast slice",
        comedy="the box made a silly little honk",
        repeated_sound="thump",
        requires="width",
        keyword="squeeze-dim",
    ),
    "hat": Task(
        id="hat",
        verb="pull the floppy hat out from the shelf",
        gerund="pulling the floppy hat from the shelf",
        attempt="wiggle the hat again",
        outcome="the hat booped the shelf and slid back",
        comedy="the hat behaved like it was playing hide-and-seek",
        repeated_sound="boing",
        requires="reach",
        keyword="repetition",
    ),
    "cushion": Task(
        id="cushion",
        verb="get the cushion past the jammed chair",
        gerund="getting the cushion past the jammed chair",
        attempt="squeeze it again",
        outcome="the cushion puffed itself up and refused to hurry",
        comedy="the cushion looked offended by the whole idea",
        repeated_sound="plop",
        requires="angle",
        keyword="comedy",
    ),
}

FIXES = {
    "turn_sideways": Fix(
        id="turn_sideways",
        label="turning sideways",
        method="turn sideways first",
        helps="saves width in a squeeze-dim space",
        result="the item slid through with a tiny shimmy",
    ),
    "use_hook": Fix(
        id="use_hook",
        label="a hook on a stick",
        method="use a hook on a stick",
        helps="reaches high shelves without climbing",
        result="the item came down with a polite plink",
    ),
    "ask_help": Fix(
        id="ask_help",
        label="asking for help",
        method="ask for help",
        helps="turns a stuck moment into teamwork",
        result="two pairs of hands made the job easy",
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Lena", "Pippa", "Owen", "Ruby", "Jasper"]
TRAITS = ["silly", "busy", "cheerful", "bouncy", "curious", "chatty"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness / selection
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for task_id in TASKS:
            if setting.crowding >= 2:
                combos.append((place, task_id))
    return combos


def choose_fix(task: Task, setting: Setting) -> Optional[Fix]:
    if task.requires == "width":
        return FIXES["turn_sideways"]
    if task.requires == "reach":
        return FIXES["use_hook"]
    return FIXES["ask_help"]


def explain_rejection() -> str:
    return "(No story: that combination is too weird for this comedy world.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _repeat_failure(world: World, hero: Entity, task: Task) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
    world.say(
        f"{hero.id} tried to {task.verb}, and then tried again, and then one more time. "
        f"Each try went {task.repeated_sound}, {task.repeated_sound}, {task.repeated_sound}."
    )
    world.say(
        f"At last, {task.outcome}. {task.comedy}."
    )


def _turn_to_fix(world: World, hero: Entity, task: Task, fix: Fix) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} stopped doing the same thing over and over. Instead, {hero.pronoun('subject')} decided to {fix.method}."
    )
    world.say(
        f"That was the trick, because it {fix.helps}, and {fix.result}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1


def tell(setting: Setting, task: Task, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={}, memes={}))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label="the helper"))

    world.say(
        f"{hero.id} was a {trait} little {hero.type} who loved making jokes while working in {setting.place}."
    )
    world.say(
        f"One day, {hero.id} wanted to {task.verb} in {setting.squeeze_dim} {setting.place}."
    )
    world.say(
        f"{hero.id} kept saying, '{task.attempt.title()}!' and the room answered back with a funny little echo."
    )

    world.para()
    _repeat_failure(world, hero, task)
    world.say(
        f"The whole scene became extra funny because {hero.id} kept repeating the same move, hoping the boxy problem would turn into a different problem."
    )

    world.para()
    fix = choose_fix(task, setting)
    if fix is None:
        raise StoryError(explain_rejection())
    world.say(
        f"{helper.label} watched the same mistake happen twice and smiled."
    )
    world.say(
        f"'{hero.id}, let's try something smarter,' {helper.label} said."
    )
    _turn_to_fix(world, hero, task, fix)

    world.say(
        f"In the end, {hero.id} finished the job, and the {task.id} was done without another {task.repeated_sound}."
    )
    world.say(
        f"{hero.id} laughed, {helper.label} laughed, and the squeeze-dim place felt a lot bigger once the repeating stopped."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        task=task,
        setting=setting,
        fix=fix,
        repeated=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    setting = f["setting"]
    return [
        f"Write a short comedy story about {hero.id} in {setting.place} where repetition causes a funny problem.",
        f"Tell a child-friendly story about a squeeze-dim place and how {hero.id} stops repeating the same failed move.",
        f"Write a funny story where {hero.id} keeps trying to {task.verb} until a smarter method works.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    setting = f["setting"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {setting.place}?",
            answer=f"{hero.id} wanted to {task.verb} in {setting.squeeze_dim} {setting.place}.",
        ),
        QAItem(
            question=f"What went funny wrong before the fix?",
            answer=f"{hero.id} kept trying again and again, but each repeat ended with {task.outcome}.",
        ),
        QAItem(
            question=f"What helped {hero.id} finish the job?",
            answer=f"{hero.id} stopped repeating the same move and used {fix.label}, which made the task work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does squeeze-dim mean?",
            answer="Squeeze-dim means very narrow or tight, so there is not much room to move around.",
        ),
        QAItem(
            question="Why can repetition be funny in a story?",
            answer="Repetition can be funny because doing the same thing over and over makes the mistake feel bigger and sillier before the clever fix arrives.",
        ),
        QAItem(
            question="What is a comedy story?",
            answer="A comedy story is a story meant to make people smile or laugh, often by using silly actions or surprising mistakes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={e.memes} meters={e.meters}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A place is squeeze-dim if it has little room.
squeeze_dim(P) :- place(P), tight(P).

% Repetition is part of the story when the hero tries the same task multiple times.
repeated(T) :- task(T).

% A task resolves when a compatible fix exists.
resolved(T) :- task(T), fix(F), helps(F, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        lines.append(asp.fact("tight", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("helps", fid, next(iter(TASKS))))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show squeeze_dim/1. #show repeated/1. #show resolved/1."))
    seen = set((sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", None) for a in sym.arguments)) for sym in model)
    expected = set()
    for p in SETTINGS:
        expected.add(("squeeze_dim", (p,)))
    for t in TASKS:
        expected.add(("repeated", (t,)))
        expected.add(("resolved", (t,)))
    if seen != expected:
        print("MISMATCH between ASP and python gate")
        return 1
    print("OK: ASP and python gate agree.")
    return 0


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy squeeze-dim repetition storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if not combos:
        raise StoryError(explain_rejection())
    place, task = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], params.name, params.gender, params.trait)
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
    StoryParams(place="closet", task="box", name="Milo", gender="boy", trait="bouncy"),
    StoryParams(place="hallway", task="hat", name="Ruby", gender="girl", trait="cheerful"),
    StoryParams(place="bus", task="cushion", name="Toby", gender="boy", trait="silly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show squeeze_dim/1. #show repeated/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show squeeze_dim/1. #show repeated/1. #show resolved/1."))
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
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
        if args.all:
            p = sample.params
            print(f"### {p.name}: {p.task} at {p.place}")
        elif len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
