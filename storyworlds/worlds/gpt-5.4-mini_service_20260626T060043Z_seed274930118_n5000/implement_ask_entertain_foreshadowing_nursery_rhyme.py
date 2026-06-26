#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a child who notices a foreshadowing clue,
asks for help, and then implements a cheerful plan so everyone can be
entertained.

The seed words are woven into the domain:
- implement: the child carries out a small plan
- ask: the child asks a helper for help
- entertain: the helper entertains a little companion
- foreshadowing: an early sign hints at the later turn
- nursery rhyme style: short, sing-song, concrete prose
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
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    clue: str
    risk: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperPlan:
    id: str
    label: str
    prep: str
    ending: str
    entertains: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, affords={"kite", "music"}),
    "porch": Setting(place="the porch", indoors=False, affords={"music", "puzzle"}),
    "nursery": Setting(place="the nursery", indoors=True, affords={"music", "puzzle"}),
}

TASKS = {
    "kite": Task(
        id="kite",
        verb="build the little kite",
        gerund="building the little kite",
        clue="the clouds went gray and the wind began to tap",
        risk="the string might tangle in the gusts",
        result="the kite might wobble and fall",
        tags={"wind", "sky"},
    ),
    "music": Task(
        id="music",
        verb="set up a song game",
        gerund="singing a song game",
        clue="the baby's feet began to wiggle before the tune had even started",
        risk="the baby might grow fussy without a merry rhyme",
        result="the room might turn prickly and sad",
        tags={"song", "baby"},
    ),
    "puzzle": Task(
        id="puzzle",
        verb="finish the bright puzzle",
        gerund="finishing the bright puzzle",
        clue="one corner piece kept hiding under the rug",
        risk="the picture might stay incomplete",
        result="the picture might never look whole",
        tags={"piece", "problem"},
    ),
}

HELPERS = {
    "bear": HelperPlan(
        id="bear",
        label="a teddy bear",
        prep="hold the little bear close and sing a soft rhyme",
        ending="the teddy bear sat smiling by the pillow",
        entertains="the baby",
        guards={"song"},
    ),
    "bells": HelperPlan(
        id="bells",
        label="a tin set of bells",
        prep="shake the tin bells in a tiny tune",
        ending="the bells gave a bright ding-ding sound",
        entertains="the puppy",
        guards={"fuss"},
    ),
    "ribbon": HelperPlan(
        id="ribbon",
        label="a striped ribbon",
        prep="twirl the striped ribbon in a little dance",
        ending="the ribbon fluttered like a tiny flag",
        entertains="the kitten",
        guards={"boredom"},
    ),
}

NAMES = ["Mina", "Pip", "Lulu", "Toby", "Nora", "Benny"]
TRAITS = ["bright", "cheery", "small", "spry", "gentle", "busy"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    helper: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A task is workable in a place when the place affords it.
workable(P, T) :- affords(P, T).

% A helper plan fits when it guards the task's need.
fits(H, T) :- helper(H), task(T), guards(H, T).

valid_story(P, T, H) :- workable(P, T), fits(H, T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", hid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for t in TASKS:
            if t in SETTINGS[p].affords:
                for h in HELPERS:
                    if t == "music" and "song" in HELPERS[h].guards:
                        combos.append((p, t, h))
                    elif t == "kite" and h == "bells":
                        combos.append((p, t, h))
                    elif t == "puzzle" and h == "ribbon":
                        combos.append((p, t, h))
    return combos


def explain_rejection(place: str, task: str, helper: str) -> str:
    return (
        f"(No story: {helper} does not fit {task} at {place}. "
        f"The child needs a helper that matches the task's foreshadowed trouble.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def nursery_opening(name: str, trait: str, task: Task) -> str:
    return (
        f"Little {name} was a {trait} child who loved a busy day. "
        f"{name} liked {task.gerund}, with a tip-tap, skip-skip way."
    )


def foreshadow_line(task: Task) -> str:
    return f"Yet {task.clue}, like a drum-beat in the air."


def ask_for_help(name: str, helper: HelperPlan, task: Task) -> str:
    return (
        f"So {name} did not rush, but stopped to ask for help. "
        f"\"Please, please,\" said {name}, \"let's keep the little day from a tangle and a sigh.\""
    )


def entertain_line(helper: HelperPlan) -> str:
    return (
        f"{helper.prep.capitalize()}. "
        f"That way, {helper.entertains} could stay entertained and sweet."
    )


def implement_line(name: str, task: Task, helper: HelperPlan) -> str:
    return (
        f"Then {name} could implement the plan, step by step, with a gentle little care. "
        f"{name} kept to {task.verb}, while {helper.ending} there."
    )


def ending_line(name: str, task: Task, helper: HelperPlan) -> str:
    return (
        f"And by the end, the worry was gone, the sky was clear and light. "
        f"{name} had {task.result}, and the day felt just right."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    task = TASKS[params.task]
    helper = HELPERS[params.helper]

    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    companion = world.add(Entity(id="helper", kind="character", type="helper", label=helper.label))
    child.memes["hope"] = 1.0
    child.memes["care"] = 1.0
    companion.memes["kind"] = 1.0

    world.facts.update(params=params, child=child, helper=companion, task=task, helper_plan=helper)
    world.say(nursery_opening(params.name, params.trait, task))
    world.say(foreshadow_line(task))
    world.say(ask_for_help(params.name, helper, task))
    world.say(entertain_line(helper))
    world.say(implement_line(params.name, task, helper))
    world.say(ending_line(params.name, task, helper))
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    task: Task = f["task"]
    helper: HelperPlan = f["helper_plan"]
    return [
        f'Write a short nursery-rhyme story for children about {p.name} and a foreshadowing clue in {SETTINGS[p.place].place}.',
        f"Tell a sing-song tale where {p.name} asks for help, {helper.label} entertains a little companion, and {p.name} implements a plan.",
        f'Write a simple story that uses the words "ask", "entertain", and "implement" in a rhyme-like way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    task: Task = f["task"]
    helper: HelperPlan = f["helper_plan"]
    place = SETTINGS[p.place].place
    return [
        QAItem(
            question=f"What did {p.name} want to do at {place}?",
            answer=f"{p.name} wanted to {task.verb} at {place}.",
        ),
        QAItem(
            question=f"What early clue hinted that trouble might come?",
            answer=f"The clue was that {task.clue}. That foreshadowed the later problem.",
        ),
        QAItem(
            question=f"How did {p.name} solve the problem?",
            answer=f"{p.name} asked for help, {helper.prep}, and then implemented the plan step by step.",
        ),
        QAItem(
            question=f"What was the ending image?",
            answer=f"By the end, {p.name} had {task.result}, and {helper.ending}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "wind": [
        QAItem(
            question="What can wind do?",
            answer="Wind can push leaves, ruffle paper, and make little things wobble.",
        )
    ],
    "song": [
        QAItem(
            question="Why do children like songs?",
            answer="Children like songs because songs can be fun to sing, easy to remember, and cheerful to hear.",
        )
    ],
    "baby": [
        QAItem(
            question="Why do babies like simple sounds?",
            answer="Babies often like simple sounds because soft rhythms and repeats are easy to enjoy.",
        )
    ],
    "piece": [
        QAItem(
            question="What is a puzzle piece?",
            answer="A puzzle piece is one small part of a bigger picture.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    task: Task = world.facts["task"]
    out: list[QAItem] = []
    for tag in sorted(task.tags):
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name", choices=NAMES)
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
    if args.place and args.task and args.helper:
        if (args.place, args.task, args.helper) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.task, args.helper))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.task is None or c[1] == args.task)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, helper = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, helper=helper, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:\n")
        for p, t, h in combos:
            print(f"  {p:8} {t:8} {h:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, task, helper in valid_combos():
            params = StoryParams(
                place=place,
                task=task,
                helper=helper,
                name=NAMES[0],
                trait=TRAITS[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
