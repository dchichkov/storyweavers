#!/usr/bin/env python3
"""
storyworlds/worlds/shuck_sound_effects_bravery_moral_value_slice.py
====================================================================

A small slice-of-life story world about shucking corn, noticing little sounds,
and choosing the brave and honest thing to do.

Premise:
- A child helps an older family member prepare food.
- The child is a little nervous about the prickly husks and the unfamiliar task.
- The work makes a satisfying shuck-shuck sound.
- Something small goes wrong.
- The child tells the truth and keeps helping anyway.

The world is constrained so each generated story feels like a complete, gentle
scene with a beginning, a turn, and an ending image that proves something
changed.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    sound: str
    risky: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    label: str
    prompt: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    task: str
    moral: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _narrate_sound(s: str) -> str:
    return {
        "shuck": "shuck-shuck",
        "snap": "snap-snap",
        "rustle": "rustle-rustle",
        "tap": "tap-tap",
    }.get(s, s)


def _introduce(world: World, child: Entity, helper: Entity, task: Task, moral: Moral) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in child.memes if t != 't') if child.memes else 'curious'} "
        f"{child.type} who liked helping {helper.pronoun('object')} in {world.setting.place}."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to {task.verb}, and the work made a soft "
        f"{_narrate_sound(task.sound)} sound."
    )
    world.say(
        f"{helper.id} smiled and said, \"Let's be brave and keep going.\""
    )


def _do_task(world: World, child: Entity, helper: Entity, task: Task, narrate: bool = True) -> None:
    child.meters[task.id] = child.meters.get(task.id, 0) + 1
    child.memes["brave"] = child.memes.get("brave", 0) + 1
    if narrate:
        world.say(f"{child.id} reached for the next ear and kept {_narrate_sound(task.sound)}ing through the pile.")


def _mistake(world: World, child: Entity, task: Task, moral: Moral) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"Then one ear slipped from {child.pronoun('possessive')} hands and dropped with a small {task.risky}."
    )
    world.say(
        f"{child.id}'s cheeks went hot, because {moral.prompt}"
    )


def _truth(world: World, child: Entity, helper: Entity, moral: Moral) -> None:
    child.memes["honest"] = child.memes.get("honest", 0) + 1
    child.memes["brave"] = child.memes.get("brave", 0) + 1
    world.say(
        f"{child.id} took a breath and told {helper.pronoun('object')} the truth right away."
    )
    world.say(
        f"{helper.id} nodded and said it was okay, because {moral.resolution}"
    )


def _finish(world: World, child: Entity, helper: Entity, task: Task, moral: Moral) -> None:
    child.memes["peace"] = child.memes.get("peace", 0) + 1
    world.say(
        f"Together they finished the pile, and the room kept its cozy {_narrate_sound(task.sound)}-filled rhythm."
    )
    world.say(
        f"At the end, {child.id} was still helping, but now {child.pronoun()} stood a little straighter, "
        f"glad {child.pronoun('subject')} had been brave and honest."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"shuck"}),
    "porch": Setting(place="the porch", affords={"shuck"}),
    "table": Setting(place="the back table", affords={"shuck"}),
}

TASKS = {
    "shuck": Task(
        id="shuck",
        verb="shuck corn",
        gerund="shucking corn",
        sound="shuck",
        risky="pop",
        keyword="shuck",
        tags={"sound", "bravery"},
    ),
    "shell": Task(
        id="shell",
        verb="shell peas",
        gerund="shelling peas",
        sound="rustle",
        risky="spill",
        keyword="shell",
        tags={"sound"},
    ),
    "crack": Task(
        id="crack",
        verb="crack walnuts",
        gerund="cracking walnuts",
        sound="snap",
        risky="crack",
        keyword="crack",
        tags={"sound", "bravery"},
    ),
}

MORALS = {
    "honesty": Moral(
        id="honesty",
        label="honesty",
        prompt="she had made a little mistake and was afraid to say so",
        resolution="telling the truth helps fix small problems before they grow",
        tags={"moral", "bravery"},
    ),
    "sharing": Moral(
        id="sharing",
        label="sharing",
        prompt="there was only one bowl left and both people wanted to use it",
        resolution="taking turns lets everyone help without a fuss",
        tags={"moral"},
    ),
    "kindness": Moral(
        id="kindness",
        label="kindness",
        prompt="the helper looked tired after a long day",
        resolution="kind words and extra help can make the work feel lighter",
        tags={"moral"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe", "Maya", "Ruby", "Ella"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Ben", "Theo", "Sam", "Max"]
HELPERS = ["grandma", "grandpa", "mom", "dad", "aunt", "uncle"]
TRAITS = ["curious", "shy", "careful", "cheerful", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, task, moral) for place, s in SETTINGS.items() for task in s.affords for moral in MORALS]


@dataclass
class ASPModel:
    pass


ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- task_id(T).
moral(M) :- moral_id(M).

valid(P,T,M) :- setting(P), can_do(P,T), task_id(T), moral_id(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for t in sorted(s.affords):
            lines.append(asp.fact("can_do", p, t))
    for t in TASKS:
        lines.append(asp.fact("task_id", t))
    for m in MORALS:
        lines.append(asp.fact("moral_id", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if a - p:
        print(" only in clingo:", sorted(a - p))
    if p - a:
        print(" only in python:", sorted(p - a))
    return 1


def tell(setting: Setting, task: Task, moral: Moral, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, memes={"trait": 1.0}))
    adult = world.add(Entity(id=helper, kind="character", type="adult"))
    _introduce(world, child, adult, task, moral)
    world.para()
    world.say(f"The day was ordinary and cozy, with {world.setting.place} full of little jobs.")
    _do_task(world, child, adult, task)
    _mistake(world, child, task, moral)
    _truth(world, child, adult, moral)
    world.para()
    _finish(world, child, adult, task, moral)
    world.facts.update(child=child, adult=adult, task=task, moral=moral)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story for a child who is {f["task"].gerund} in {world.setting.place}, with a clear sound effect like "{f["task"].keyword}".',
        f"Tell a short story where {f['child'].id} is brave while helping {f['adult'].id} and learns {f['moral'].label}.",
        f'Write a small everyday story that includes the word "{f["task"].keyword}" and ends with an honest choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, task, moral = f["child"], f["adult"], f["task"], f["moral"]
    return [
        QAItem(
            question=f"What was {child.id} doing in {world.setting.place}?",
            answer=f"{child.id} was {task.gerund} to help {adult.id}.",
        ),
        QAItem(
            question=f"What sound did the work make?",
            answer=f"It made a soft {task.sound}-shuck sound while they worked.",
        ),
        QAItem(
            question=f"Why did {child.id} feel nervous after the small mistake?",
            answer=f"{child.id} worried because {moral.prompt}.",
        ),
        QAItem(
            question=f"What brave choice did {child.id} make?",
            answer=f"{child.id} told {adult.pronoun('object')} the truth right away.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"They finished the work together, and {child.id} stayed calm, honest, and helpful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to shuck corn?",
            answer="To shuck corn means to pull off the green husk and silk around the ear of corn.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous or scared.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth instead of hiding a mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.kind}/{e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", task="shuck", moral="honesty", name="Mia", gender="girl", helper="grandma", trait="curious"),
    StoryParams(place="porch", task="shuck", moral="kindness", name="Leo", gender="boy", helper="mom", trait="shy"),
    StoryParams(place="table", task="shuck", moral="sharing", name="Nora", gender="girl", helper="dad", trait="careful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("unknown place")
    if args.task and args.task not in TASKS:
        raise StoryError("unknown task")
    if args.moral and args.moral not in MORALS:
        raise StoryError("unknown moral")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.moral is None or c[2] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task, moral = rng.choice(sorted(combos))
    task_obj = TASKS[task]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, moral=moral, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task], MORALS[params.moral], params.name, params.gender, params.helper, params.trait)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about shucking corn, bravery, and honesty.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--moral", choices=sorted(MORALS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
