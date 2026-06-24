#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/executive_redundancy_aggravate_repetition_kindness_transformation_slice.py
=====================================================================================================================

A small slice-of-life storyworld about an executive, a repeated work task, and a
kindness-driven transformation.

Seed tale inspiration:
---
An executive named Priya kept seeing the same note copied into every weekly report.
The repetition made the work pile up, and the extra pages began to aggravate her.

One afternoon, Priya paused, looked at the team, and realized the repeated steps
were slowing everyone down. Instead of scolding anyone, she asked gentle questions
and listened carefully. A teammate pointed out that the same update was being
written in three different places.

Priya smiled, simplified the process, and thanked the team for speaking kindly
and honestly. After that, the reports became shorter, the room felt lighter, and
the work got done with less fuss.

Causal shape:
---
    repeated task load -> office friction
    friction + kindness -> clearer conversation
    clearer conversation -> transformed workflow
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

NAMES = ["Priya", "Mina", "Jordan", "Sana", "Eli", "Tara", "Noah", "Iris"]
ROLES = ["executive", "manager", "director"]
TEAMS = ["team", "group", "office"]
PLACES = ["the office", "the conference room", "the meeting room", "the corner desk"]
TASKS = [
    ("weekly report", "write the weekly report", "writing the weekly report"),
    ("status update", "send the status update", "sending the status update"),
    ("project note", "copy the project note", "copying the project note"),
    ("meeting summary", "share the meeting summary", "sharing the meeting summary"),
]
TENSIONS = ["repetition", "redundancy", "extra steps", "duplicate notes"]

ASP_RULES = r"""
repeated(T) :- task(T), repeats(T), load(T).
aggravates(T) :- repeated(T), extra_pages(T).
kind_interaction(W) :- kindness(W), hears(W), repeated(T), load(T).
transforms(W) :- kind_interaction(W), simplifies(W).
better_workflow :- transforms(_).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    role: str = ""
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    role: str
    place: str
    task: str
    seed_word: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = _copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _apply_repetition(world: World) -> list[str]:
    out: list[str] = []
    execu = world.entities["executive"]
    task = world.entities["task"]
    if task.meters.get("repeated", 0.0) < THRESHOLD:
        return out
    if ("aggravate", task.id) in world.fired:
        return out
    world.fired.add(("aggravate", task.id))
    execu.memes["aggravation"] = execu.memes.get("aggravation", 0.0) + 1
    out.append(f"The repeated task kept piling up and made the room feel tense.")
    return out


def _apply_kindness(world: World) -> list[str]:
    out: list[str] = []
    execu = world.entities["executive"]
    helper = world.entities["helper"]
    task = world.entities["task"]
    if execu.memes.get("aggravation", 0.0) < THRESHOLD:
        return out
    if helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("transform", task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    task.meters["simplified"] = task.meters.get("simplified", 0.0) + 1
    execu.memes["relief"] = execu.memes.get("relief", 0.0) + 1
    out.append("A kind conversation helped everyone see a simpler way.")
    out.append("The repeated steps changed into one clear step.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_apply_repetition, _apply_kindness):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(place=params.place)
    execu = world.add(Entity(id="executive", kind="character", role=params.role, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", role="teammate", label="the teammate"))
    task = world.add(Entity(id="task", kind="thing", label=params.task))
    world.facts.update(executive=execu, helper=helper, task=task)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    execu = world.entities["executive"]
    helper = world.entities["helper"]
    task = world.entities["task"]

    world.say(f"{execu.label} was a {execu.role} who worked at {world.place}.")
    world.say(f"Every week, {execu.label} had to {task.label}, and the same note kept appearing again and again.")
    world.say("That repetition started to aggravate the whole day.")

    world.para()
    world.say(f"One afternoon, {execu.label} noticed the extra steps and paused before speaking too quickly.")
    world.say(f"Instead of getting sharp, {execu.label} chose kindness and asked the team gentle questions.")
    helper.memes["kindness"] = 1.0
    task.meters["repeated"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"The teammate pointed out where the duplicate note was being copied.")
    world.say(f"{execu.label} smiled, removed the extra step, and thanked everyone for helping.")
    world.say(f"By the end of the day, the work felt lighter, and {execu.label} could finish {task.label} with less fuss.")

    world.facts.update(
        repetition=True,
        kindness=True,
        transformation=True,
        task_label=params.task,
        seed_word=params.seed_word,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story about an {f["executive"].role} dealing with {f["seed_word"]} and {f["task_label"]}.',
        f"Tell a gentle office story where repetition starts to aggravate the day, but kindness changes the workflow.",
        f"Write a small story about an executive, a repeated task, and a kind transformation at work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    execu = f["executive"]
    helper = f["helper"]
    task = f["task"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {execu.label}, an {execu.role} who works at {world.place}.",
        ),
        QAItem(
            question=f"What kept happening again and again in the story?",
            answer=f"The same {task.label} kept showing up again and again, which made the work feel repetitive.",
        ),
        QAItem(
            question=f"What did {execu.label} choose instead of getting upset?",
            answer=f"{execu.label} chose kindness, asked gentle questions, and listened to the team.",
        ),
        QAItem(
            question=f"How did the work change by the end?",
            answer=f"The extra steps were removed, the task became simpler, and the day felt calmer and easier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an executive?",
            answer="An executive is a person who helps lead a business or organization and makes important work decisions.",
        ),
        QAItem(
            question="What is redundancy?",
            answer="Redundancy means something is repeated more than needed, so it adds extra copies or extra steps.",
        ),
        QAItem(
            question="What does kindness do in a team?",
            answer="Kindness helps people speak gently, listen better, and work together without making the problem worse.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one way of being to a new way of being.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "executive"),
        asp.fact("character", "helper"),
        asp.fact("task", "task"),
        asp.fact("repeats", "task"),
        asp.fact("load", "task"),
        asp.fact("kindness", "helper"),
        asp.fact("hears", "helper"),
        asp.fact("simplifies", "helper"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show repeated/1.\n#show aggravates/1.\n#show better_workflow/0."))
    repeated = set(asp.atoms(model, "repeated"))
    aggravates = set(asp.atoms(model, "aggravates"))
    better = set(asp.atoms(model, "better_workflow"))
    ok = repeated == {("task",)} and aggravates == {("task",)} and better == {()}
    if ok:
        print("OK: ASP rules are internally consistent.")
        return 0
    print("MISMATCH: ASP rules did not derive the expected facts.")
    print("repeated:", sorted(repeated))
    print("aggravates:", sorted(aggravates))
    print("better_workflow:", sorted(better))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about executive redundancy, kindness, and transformation.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=[t[0] for t in TASKS])
    ap.add_argument("--seed-word", choices=["executive", "redundancy", "aggravate", "Repetition", "Kindness", "Transformation"])
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
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    place = args.place or rng.choice(PLACES)
    task = args.task or rng.choice([t[0] for t in TASKS])
    seed_word = args.seed_word or rng.choice(["executive", "redundancy", "aggravate", "Repetition", "Kindness", "Transformation"])
    return StoryParams(name=name, role=role, place=place, task=task, seed_word=seed_word)


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


CURATED = [
    StoryParams(name="Priya", role="executive", place="the office", task="weekly report", seed_word="repetition"),
    StoryParams(name="Mina", role="director", place="the conference room", task="status update", seed_word="Kindness"),
    StoryParams(name="Jordan", role="manager", place="the meeting room", task="meeting summary", seed_word="Transformation"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repeated/1.\n#show aggravates/1.\n#show better_workflow/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show repeated/1.\n#show aggravates/1.\n#show better_workflow/0."))
        print("repeated:", sorted(set(asp.atoms(model, "repeated"))))
        print("aggravates:", sorted(set(asp.atoms(model, "aggravates"))))
        print("better_workflow:", sorted(set(asp.atoms(model, "better_workflow"))))
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
            i += 1
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
            header = f"### {p.name}: {p.role} at {p.place} ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
