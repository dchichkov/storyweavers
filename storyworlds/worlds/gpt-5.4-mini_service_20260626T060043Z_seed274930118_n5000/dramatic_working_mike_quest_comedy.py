#!/usr/bin/env python3
"""
storyworlds/worlds/dramatic_working_mike_quest_comedy.py
=========================================================

A small comedy storyworld about a working day that turns into a silly quest.

Premise:
A child-friendly workplace has a dramatic little problem: Mike needs to finish
a simple task, but one missing thing sends everyone on a quest through the room.
The tension is mild, the solution is practical, and the ending is a cheerful
laugh when the right tool is found.

This world is intentionally compact:
- one setting
- one hero
- one helper
- one quest item
- one obstacle
- one resolution

The story is driven by state changes:
- the task is stalled when a needed item is missing
- a search quest begins
- helpful clues reduce confusion
- the quest item is found and the task is completed
- the emotional state shifts from dramatic worry to comic relief
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
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "office": {
        "place": "the office",
        "descriptor": "bright and tidy",
        "supports": {"task", "quest"},
    },
    "workshop": {
        "place": "the workshop",
        "descriptor": "busy and noisy",
        "supports": {"task", "quest"},
    },
    "library": {
        "place": "the library corner",
        "descriptor": "quiet with soft chairs",
        "supports": {"task", "quest"},
    },
}

TASKS = {
    "paperstack": {
        "label": "paper stack",
        "verb": "sort the paper stack",
        "progress": "sorting pages",
        "mess": "scattered",
        "missing": "sticker",
        "problem": "the papers would slide around",
    },
    "model": {
        "label": "model kit",
        "verb": "finish the model kit",
        "progress": "building tiny pieces",
        "mess": "unfinished",
        "missing": "blue screw",
        "problem": "the little parts would not stay together",
    },
    "poster": {
        "label": "poster",
        "verb": "hang the poster",
        "progress": "lining up corners",
        "mess": "crooked",
        "missing": "tape",
        "problem": "it would keep flopping down",
    },
}

QUEST_ITEMS = {
    "tape": {
        "label": "a roll of tape",
        "place": "under the desk",
        "clue": "sticky and round",
        "fixes": {"poster"},
        "purpose": "hold the poster up",
    },
    "sticker": {
        "label": "a bright sticker",
        "place": "on the shelf",
        "clue": "small and shiny",
        "fixes": {"paperstack"},
        "purpose": "keep the papers neat",
    },
    "blue_screw": {
        "label": "a tiny blue screw",
        "place": "in the parts tray",
        "clue": "tiny and blue",
        "fixes": {"model"},
        "purpose": "connect the model pieces",
    },
}

HELPERS = {
    "nina": {
        "name": "Nina",
        "role": "coworker",
        "style": "practical",
        "joke": "always knew where the missing things hid",
    },
    "otto": {
        "name": "Otto",
        "role": "helper",
        "style": "patient",
        "joke": "could spot a clue faster than anyone",
    },
    "zoe": {
        "name": "Zoe",
        "role": "friend",
        "style": "cheerful",
        "joke": "smiled even when the search looked silly",
    },
}

HERO_NAMES = ["Mike", "Mikey", "Michael"]
TRAITS = ["dramatic", "working", "curious", "silly", "careful"]


# ---------------------------------------------------------------------------
# Shared entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    moved: bool = False
    found: bool = False
    fixed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "he" if self.type in {"boy", "man"} else "they" if self.kind == "group" else "it"

    def possessive(self) -> str:
        return "his" if self.type in {"boy", "man"} else "their" if self.kind == "group" else "its"


@dataclass
class StoryParams:
    setting: str
    task: str
    quest_item: str
    hero_name: str = "Mike"
    helper: str = "nina"
    trait: str = "dramatic"
    seed: Optional[int] = None


class World:
    def __init__(self, setting_key: str) -> None:
        self.setting_key = setting_key
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _start_task(world: World, hero: Entity, task_key: str) -> None:
    task = TASKS[task_key]
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    world.say(
        f"{hero.id} was ready to {task['verb']}, but the day felt oddly dramatic "
        f"because {task['label']} needed one small thing first."
    )


def _missing_problem(world: World, hero: Entity, task_key: str, quest_item_key: str) -> None:
    task = TASKS[task_key]
    quest_item = QUEST_ITEMS[quest_item_key]
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"Then {hero.id} noticed the {task['missing']} was gone. Without it, "
        f"{task['problem']}."
    )
    world.say(
        f'{hero.id} put on a very dramatic face and said, "This is a quest!" '
        f'Everyone had to laugh a little, because it was only a tiny quest.'
    )


def _search(world: World, hero: Entity, helper: Entity, quest_item_key: str) -> None:
    quest_item = QUEST_ITEMS[quest_item_key]
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0.0) + 1
    hero.memes["determination"] = hero.memes.get("determination", 0.0) + 1
    world.say(
        f"{helper.id} pointed toward {quest_item['place']} and said the clue was "
        f"{quest_item['clue']}."
    )
    world.say(
        f"So {hero.id} went on a small quest, peeking behind things and checking "
        f"the corners one by one."
    )


def _find_item(world: World, hero: Entity, quest_item_key: str) -> Entity:
    quest_item = QUEST_ITEMS[quest_item_key]
    item = world.add(Entity(
        id=quest_item_key,
        label=quest_item["label"],
        type="tool",
        found=True,
    ))
    world.say(
        f"At last, {hero.id} found {quest_item['label']} {quest_item['place']}. "
        f"It had been hiding there the whole time."
    )
    return item


def _finish_task(world: World, hero: Entity, task_key: str, quest_item: Entity) -> None:
    task = TASKS[task_key]
    quest = QUEST_ITEMS[quest_item.id]
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} used {quest['label']} to {quest['purpose']}, and suddenly "
        f"{task['label']} was no longer a problem."
    )
    world.say(
        f"With that, {hero.id} finished {task['verb']} and grinned at the silly "
        f"little adventure."
    )


def tell(setting_key: str, task_key: str, quest_item_key: str, hero_name: str, helper_key: str, trait: str) -> World:
    world = World(setting_key)
    setting = SETTINGS[setting_key]
    helper_cfg = HELPERS[helper_key]

    hero = world.add(Entity(id=hero_name, kind="character", type="boy"))
    helper = world.add(Entity(id=helper_cfg["name"], kind="character", type="girl" if helper_key != "otto" else "boy"))
    task = world.add(Entity(id=task_key, label=TASKS[task_key]["label"], type="thing"))
    quest_item = world.add(Entity(id=quest_item_key, label=QUEST_ITEMS[quest_item_key]["label"], type="tool"))

    world.facts.update(
        hero=hero,
        helper=helper,
        task=task,
        quest_item=quest_item,
        setting=setting,
        trait=trait,
        helper_role=helper_cfg["role"],
    )

    world.say(
        f"{hero.id} was a {trait} working kid in {setting['place']}, and the place "
        f"looked {setting['descriptor']}."
    )
    world.say(
        f"He wanted to finish the {task.label}, because he liked making things go right."
    )

    world.para()
    _start_task(world, hero, task_key)
    _missing_problem(world, hero, task_key, quest_item_key)

    world.para()
    world.say(
        f"{helper.id}, the {helper_cfg['role']}, stayed calm and gave a clue. "
        f"That turned the problem into a quest instead of a panic."
    )
    _search(world, hero, helper, quest_item_key)

    world.para()
    found = _find_item(world, hero, quest_item_key)
    _finish_task(world, hero, task_key, found)

    world.para()
    world.say(
        f"In the end, {hero.id} got the work done, {helper.id} laughed, and the "
        f"tiny quest became the best part of the day."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    quest_item = f["quest_item"]
    helper = f["helper"]
    trait = f["trait"]
    setting = f["setting"]
    return [
        f'Write a short comedy story about {f["hero"].id} in {setting["place"]} who has a {TASKS[task.id]["label"]} problem and starts a quest.',
        f"Tell a funny story where {f['hero'].id}, a {trait} working kid, needs {QUEST_ITEMS[quest_item.id]['label']} to finish the job.",
        f"Write a child-friendly story about a tiny workplace quest, a helpful friend, and a silly dramatic moment.",
        f"Make a short story with the words dramatic, working, and mike, and end with the task finally being done.",
        f"Tell a comedy story where {helper.id} gives a clue that helps solve the missing {QUEST_ITEMS[quest_item.id]['label']} mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    task = f["task"]
    item = f["quest_item"]
    setting = f["setting"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a {trait} working kid in {setting['place']}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to finish?",
            answer=f"{hero.id} wanted to finish the {task.label}.",
        ),
        QAItem(
            question=f"What was missing at first?",
            answer=f"The missing thing was {item.label}.",
        ),
        QAItem(
            question=f"Who helped turn the problem into a quest?",
            answer=f"{helper.id} helped by giving a clue and staying calm.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} found the missing item, finished the task, and laughed with {helper.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip or search to find something or solve a problem.",
        ),
        QAItem(
            question="Why is a clue helpful?",
            answer="A clue helps by pointing someone toward the thing they need to find.",
        ),
        QAItem(
            question="Why can a missing tool slow down work?",
            answer="If a tool is missing, the job may have to wait until the tool is found.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(office).
setting(workshop).
setting(library).

task(paperstack).
task(model).
task(poster).

quest_item(tape).
quest_item(sticker).
quest_item(blue_screw).

hero(mike).

% A task needs one item to be finished.
needs(paperstack, sticker).
needs(model, blue_screw).
needs(poster, tape).

% The quest is valid when a task has a matching missing item.
valid_story(S, T, Q) :- setting(S), task(T), quest_item(Q), needs(T, Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for qid in QUEST_ITEMS:
        lines.append(asp.fact("quest_item", qid))
    lines.append(asp.fact("hero", "mike"))
    for tid, cfg in TASKS.items():
        for qid, qcfg in QUEST_ITEMS.items():
            if qid in qcfg["fixes"]:
                lines.append(asp.fact("needs", tid, qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((s, t, q) for s in SETTINGS for t in TASKS for q in QUEST_ITEMS if q in QUEST_ITEMS[q]["fixes"] and s in SETTINGS)
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python reasonableness check ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic quest storyworld about Mike and a missing work item.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--quest-item", dest="quest_item", choices=QUEST_ITEMS)
    ap.add_argument("--name", default="Mike")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
    quest_item = args.quest_item or rng.choice([qid for qid, cfg in QUEST_ITEMS.items() if task in cfg["fixes"]])
    if task not in QUEST_ITEMS[quest_item]["fixes"]:
        raise StoryError("That quest item does not fit the task, so the story would not resolve honestly.")
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(list(TRAITS))
    return StoryParams(
        setting=setting,
        task=task,
        quest_item=quest_item,
        hero_name=args.name or "Mike",
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.task, params.quest_item, params.hero_name, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    lines.extend(f"event: {t}" for t in world.trace)
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


CURATED = [
    StoryParams(setting="office", task="poster", quest_item="tape", hero_name="Mike", helper="nina", trait="dramatic"),
    StoryParams(setting="workshop", task="model", quest_item="blue_screw", hero_name="Mike", helper="otto", trait="working"),
    StoryParams(setting="library", task="paperstack", quest_item="sticker", hero_name="Mike", helper="zoe", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        for row in sorted(set(asp.atoms(model, "valid_story"))):
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
