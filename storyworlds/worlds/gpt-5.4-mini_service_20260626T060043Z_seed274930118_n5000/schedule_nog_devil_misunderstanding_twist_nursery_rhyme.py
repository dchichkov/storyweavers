#!/usr/bin/env python3
"""
storyworlds/worlds/schedule_nog_devil_misunderstanding_twist_nursery_rhyme.py
==============================================================================

A small storyworld in nursery-rhyme style about a strict schedule, a cup of nog,
and a devil-shaped misunderstanding that turns into a gentle twist.

Seed tale sketch:
---
Little Pip loved the holiday schedule. Each hour had a rhyme, each rhyme had a
task, and Pip liked to follow the list from top to bottom. But one frosty
evening, a devil came to the door. Pip gasped, because the devil had a long red
tail and a pitchfork-shaped spoon. "A devil!" Pip cried. "You're here to spoil
the nog and smash the plan!" Yet the devil only wanted to help stir the nog for
the town feast. The misunderstanding melted away, and Pip learned that some
scary-looking things are only helpers in disguise.

World idea:
- Physical meters: spillage, delay, warmth, tidiness, helped_stir
- Emotional memes: worry, misunderstanding, relief, pride, trust
- The schedule is a tiny chain of tasks that can be kept, delayed, or repaired.
- The nog is a warm holiday drink that can spill if the setup goes wrong.
- The devil is not cruel here; it only looks alarming until the twist reveals
  it is a helper with a small mixing job.

Story shape:
- Beginning: Pip loves the schedule and the nog.
- Middle: a horned visitor appears; Pip misunderstands and worries.
- Twist: the visitor is actually here to help with the nog.
- Ending: the schedule is back on track, and the feast begins with warm cups.

This script is self-contained and uses the shared result containers from
storyworlds/results.py. ASP is supported through an inline rule twin.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "maid"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "lad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class ScheduleStep:
    hour: int
    title: str
    action: str
    location: str = ""


@dataclass
class StoryParams:
    setting: str
    name: str
    age: str
    parent: str
    schedule: str
    nog: str
    devil: str
    seed: Optional[int] = None


SETTINGS = {
    "village": "the little village green",
    "kitchen": "the warm kitchen",
    "hall": "the town hall",
    "cottage": "the snug cottage",
}

SCHEDULES = {
    "feast": [
        ScheduleStep(1, "count the cups", "count the cups", "the kitchen"),
        ScheduleStep(2, "stir the nog", "stir the nog", "the kitchen"),
        ScheduleStep(3, "carry the lanterns", "carry the lanterns", "the hall"),
        ScheduleStep(4, "sing the rhyme", "sing the rhyme", "the hall"),
    ],
    "tea": [
        ScheduleStep(1, "set the table", "set the table", "the cottage"),
        ScheduleStep(2, "warm the nog", "warm the nog", "the kitchen"),
        ScheduleStep(3, "open the door", "open the door", "the cottage"),
    ],
}

NOGS = {
    "honey nog": {"warmth": 1.0, "spill_risk": 0.6, "word": "honey nog"},
    "spiced nog": {"warmth": 1.2, "spill_risk": 0.7, "word": "spiced nog"},
    "vanilla nog": {"warmth": 0.9, "spill_risk": 0.5, "word": "vanilla nog"},
}

DEVILS = {
    "red devil": {
        "label": "a red devil",
        "phrase": "a little red devil with shiny boots and a pitchfork-shaped spoon",
        "helpful": True,
        "job": "stir the nog",
    },
    "horned devil": {
        "label": "a horned devil",
        "phrase": "a horned devil carrying a lantern and a sack of cinnamon",
        "helpful": True,
        "job": "bring the cinnamon",
    },
    "tiny devil": {
        "label": "a tiny devil",
        "phrase": "a tiny devil in a striped scarf",
        "helpful": True,
        "job": "warm the cups",
    },
}

NAMES = ["Pip", "Milo", "Nina", "Tessa", "Bram", "Luna"]
AGES = ["little", "small", "tiny", "young"]


class World:
    def __init__(self, setting: str, schedule_key: str, nog_key: str, devil_key: str) -> None:
        self.setting = setting
        self.schedule_key = schedule_key
        self.nog_key = nog_key
        self.devil_key = devil_key
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World(self.setting, self.schedule_key, self.nog_key, self.devil_key)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def init_state(world: World, child: Entity, parent: Entity, nog: Entity, devil: Entity) -> None:
    child.meters.update({"delay": 0.0, "tidiness": 1.0})
    child.memes.update({"joy": 1.0, "worry": 0.0, "misunderstanding": 0.0, "relief": 0.0, "trust": 0.0})
    parent.memes.update({"calm": 1.0, "pride": 0.0})
    nog.meters.update({"warmth": NOGS[world.nog_key]["warmth"], "spilled": 0.0})
    devil.meters.update({"helped_stir": 0.0})
    devil.memes.update({"kindness": 1.0, "mystery": 1.0})


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    child = world.get("child")
    devil = world.get("devil")
    if child.memes["misunderstanding"] < THRESHOLD:
        return out
    sig = ("mis",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1.0
    child.meters["delay"] += 1.0
    out.append(f"Little {child.id} felt a wobble of worry and forgot the next rhyme.")
    if devil.meters["helped_stir"] >= THRESHOLD:
        child.memes["misunderstanding"] = 0.0
    return out


def _r_help(world: World) -> list[str]:
    out = []
    child = world.get("child")
    devil = world.get("devil")
    nog = world.get("nog")
    if devil.meters["helped_stir"] < THRESHOLD:
        return out
    sig = ("help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    nog.meters["spilled"] = 0.0
    nog.meters["warmth"] += 0.3
    child.memes["relief"] += 1.0
    child.memes["worry"] = 0.0
    child.memes["trust"] += 1.0
    out.append("The devil only stirred the nog, and the cup grew warm and neat.")
    return out


def _r_pride(world: World) -> list[str]:
    out = []
    parent = world.get("parent")
    child = world.get("child")
    if child.memes["relief"] < THRESHOLD:
        return out
    sig = ("pride",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["pride"] += 1.0
    out.append(f"{parent.id} smiled, proud that {child.id} had learned a kinder guess.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_misunderstanding, _r_help, _r_pride):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World(params.setting, params.schedule, params.nog, params.devil)
    child = world.add(Entity("child", kind="character", type="boy", label=params.name, traits=[params.age, "careful"]))
    parent = world.add(Entity("parent", kind="character", type=params.parent, label=params.parent))
    nog = world.add(Entity("nog", type="drink", label=params.nog, phrase=params.nog))
    devil = world.add(Entity("devil", type="visitor", label=params.devil, phrase=DEVILS[params.devil]["phrase"]))

    init_state(world, child, parent, nog, devil)

    steps = SCHEDULES[params.schedule]
    world.say(f"Little {child.id} loved the schedule in {SETTINGS[params.setting]}.")
    world.say(f"Each hour had a task, and each task had a tidy place to go.")
    world.say(f"{child.id} also loved {nog.label}, warm as a mitten in winter.")

    world.para()
    world.say(f"At the first bell, {child.id} {steps[0].action} by the bright window.")
    world.say(f"At the second bell, {child.id} waited for {nog.label} to be ready.")

    world.para()
    world.say(f"Then came {devil.label}, {devil.phrase}.")
    world.say(f"{child.id} gasped and thought the {devil.label} had come to spoil the plan.")
    child.memes["misunderstanding"] += 1.0
    propagate(world)

    world.say(f'"No, no," said {parent.id}, "the {devil.label} is only here to {DEVILS[params.devil]["job"]}."')
    devil.meters["helped_stir"] += 1.0
    world.say(f"The little devil gave the nog a careful turn with the spoon.")
    propagate(world)

    world.para()
    world.say(f"Then the third bell rang, and the schedule was back on its feet.")
    world.say(f"{child.id} carried the cups to the table, and nobody spilled a drop.")
    world.say(f"At the last bell, the whole room sang a rhyme, warm with peace and nog.")
    world.say(f"{child.id} waved to the {devil.label}, no longer afraid, and smiled with trust.")
    world.facts.update(child=child, parent=parent, nog=nog, devil=devil, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short nursery-rhyme story about a child named {p.name} who follows a {p.schedule} schedule, sips {p.nog}, and meets {p.devil}.',
        f"Tell a gentle story where {p.name} first misunderstands {p.devil} but learns it is a helper, with a twist at the end.",
        f'Write a rhyme-like story that includes the words "schedule", "{p.nog}", and "devil" in a cozy holiday scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    nog = world.facts["nog"]
    devil = world.facts["devil"]
    return [
        QAItem(
            question=f"What was {child.label} trying to do with the schedule?",
            answer=f"{child.label} was trying to follow the {p.schedule} schedule step by step, from the first bell to the last.",
        ),
        QAItem(
            question=f"Why did {child.label} first worry about the {devil.label}?",
            answer=f"{child.label} saw {devil.phrase} and thought the {devil.label} had come to spoil the plan and the {nog.label}.",
        ),
        QAItem(
            question=f"What was the twist about the {devil.label}?",
            answer=f"The twist was that the {devil.label} was not there to cause trouble. It only came to help stir the {nog.label} and keep the feast going.",
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"{child.label} felt relieved, trusted the helper, and finished the evening with the cups, the rhyme, and the schedule all in order.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question="What is a schedule?",
            answer="A schedule is a plan that tells what should happen at each time, one step after another.",
        ),
        QAItem(
            question=f"What is {p.nog}?",
            answer=f"{p.nog.capitalize()} is a warm holiday drink, often served in a cup when people want something cozy.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding is when someone guesses the wrong meaning and feels worried before the truth is clear.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the reader thought was happening.",
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
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Setting, Schedule, Nog) :- setting(Setting), schedule(Schedule), nog(Nog).
valid_story(Setting, Schedule, Nog, Devil) :- valid(Setting, Schedule, Nog), devil(Devil).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for sch in SCHEDULES:
        lines.append(asp.fact("schedule", sch))
    for n in NOGS:
        lines.append(asp.fact("nog", n))
    for d in DEVILS:
        lines.append(asp.fact("devil", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((s, sch, n) for s in SETTINGS for sch in SCHEDULES for n in NOGS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python registry:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: schedule, nog, and devil.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--schedule", choices=SCHEDULES)
    ap.add_argument("--nog", choices=NOGS)
    ap.add_argument("--devil", choices=DEVILS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--age", choices=AGES)
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
    schedule = args.schedule or rng.choice(list(SCHEDULES))
    nog = args.nog or rng.choice(list(NOGS))
    devil = args.devil or rng.choice(list(DEVILS))
    name = args.name or rng.choice(NAMES)
    age = args.age or rng.choice(AGES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, name=name, age=age, parent=parent, schedule=schedule, nog=nog, devil=devil)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, schedule, nog) combos; {len(stories)} with devil:\n")
        for setting, schedule, nog in triples:
            devils = sorted(d for (s, sch, n, d) in stories if (s, sch, n) == (setting, schedule, nog))
            print(f"  {setting:8} {schedule:8} {nog:12} [{', '.join(devils)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for schedule in SCHEDULES:
                for nog in NOGS:
                    for devil in DEVILS:
                        params = StoryParams(
                            setting=setting,
                            name="Pip",
                            age="little",
                            parent="mother",
                            schedule=schedule,
                            nog=nog,
                            devil=devil,
                        )
                        samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.schedule} / {p.nog} / {p.devil}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
