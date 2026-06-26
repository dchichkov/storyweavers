#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/report_repetition_surprise_problem_solving_animal_story.py
======================================================================================================

A small animal-story world built from a seed about a report, with
repetition, surprise, and problem solving as the core narrative instruments.

Premise:
- An animal messenger wants to finish a report for the day's meeting.
- Repetition appears as the animal tries the same task several times.
- Surprise appears when a new clue or helper changes the plan.
- Problem solving appears when the animals use a practical fix to complete
  the report and calm the situation.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- shared QA/result containers imported eagerly
- ASP helpers imported lazily
- deterministic world simulation with meters and memes
- invalid explicit choices raise StoryError
- inline ASP twin and Python reasonableness gate
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
    carried_by: Optional[str] = None
    prepared: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "cat", "rabbit", "owl", "squirrel"}
        male = {"dog", "bear", "badger", "moose", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    repetition: str
    surprise: str
    fix: str
    snag: str
    result: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    affected_by: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "meadow": Setting(place="the meadow", supports={"birdsong", "berries", "wind"}),
    "pond": Setting(place="the pond", supports={"water", "duck", "reeds"}),
    "forest": Setting(place="the forest clearing", supports={"acorn", "leaf", "wind"}),
}

TASKS = {
    "berries": Task(
        id="berries",
        verb="gather berries",
        repetition="gathering one more berry, then one more berry",
        surprise="a berry basket slipped out from behind a stump",
        fix="use the basket to sort the berries by color",
        snag="the berries kept rolling away",
        result="the report could list the berries in neat rows",
        keyword="report",
        tags={"fruit", "basket"},
    ),
    "birds": Task(
        id="birds",
        verb="watch birds",
        repetition="watching one bird hop, then another bird hop",
        surprise="an owl left a feather with tiny notes on it",
        fix="copy the notes onto a leaf page",
        snag="the birds flew too fast to count",
        result="the report could count the birds without guessing",
        keyword="report",
        tags={"bird", "feather"},
    ),
    "water": Task(
        id="water",
        verb="measure water",
        repetition="measuring one puddle, then one more puddle",
        surprise="the frog pointed to a hidden spring under the reeds",
        fix="use the spring as the real water source in the report",
        snag="the puddles kept changing after the breeze",
        result="the report could explain where the water came from",
        keyword="report",
        tags={"water", "frog"},
    ),
}

ITEMS = {
    "leaf_page": Item(
        id="leaf_page",
        label="leaf page",
        phrase="a big flat leaf page",
        kind="paper",
        affected_by={"wind"},
    ),
    "basket": Item(
        id="basket",
        label="basket",
        phrase="a little woven basket",
        kind="container",
        affected_by={"berries"},
    ),
    "inkstone": Item(
        id="inkstone",
        label="inkstone",
        phrase="a smooth stone for making ink marks",
        kind="tool",
        affected_by={"water"},
    ),
}

ANIMALS = {
    "fox": ("fox", ["clever", "quick"]),
    "rabbit": ("rabbit", ["tiny", "careful"]),
    "owl": ("owl", ["quiet", "wise"]),
    "bear": ("bear", ["big", "steady"]),
    "squirrel": ("squirrel", ["bouncy", "busy"]),
    "frog": ("frog", ["small", "spry"]),
}

NAMES = {
    "fox": ["Fenn", "Ruby", "Tala"],
    "rabbit": ["Milo", "Nia", "Pip"],
    "owl": ["Orla", "Mira", "Noor"],
    "bear": ["Bruno", "Bram", "Toby"],
    "squirrel": ["Sia", "Penny", "Luma"],
    "frog": ["Finn", "Gus", "Tiko"],
}


@dataclass
class StoryParams:
    setting: str
    task: str
    hero_kind: str
    hero_name: str
    helper_kind: str
    seed: Optional[int] = None


def is_reasonable(setting: Setting, task: Task) -> bool:
    return task.id in setting.supports or bool(setting.supports & task.tags)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with a report, repetition, surprise, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero-kind", choices=sorted(ANIMALS))
    ap.add_argument("--helper-kind", choices=sorted(ANIMALS))
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
    if args.setting and args.task:
        if not is_reasonable(SETTINGS[args.setting], TASKS[args.task]):
            raise StoryError(f"(No story: {TASKS[args.task].verb} does not fit naturally at {SETTINGS[args.setting].place}.)")
    combos = []
    for s_id, setting in SETTINGS.items():
        for t_id, task in TASKS.items():
            if args.setting and s_id != args.setting:
                continue
            if args.task and t_id != args.task:
                continue
            if not is_reasonable(setting, task):
                continue
            for hero in ANIMALS:
                if args.hero_kind and hero != args.hero_kind:
                    continue
                for helper in ANIMALS:
                    if helper == hero:
                        continue
                    if args.helper_kind and helper != args.helper_kind:
                        continue
                    combos.append((s_id, t_id, hero, helper))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s_id, t_id, hero, helper = rng.choice(sorted(combos))
    return StoryParams(
        setting=s_id,
        task=t_id,
        hero_kind=hero,
        hero_name=args.name or rng.choice(NAMES[hero]),
        helper_kind=helper,
    )


def make_entity(kind: str, name: str, label: str = "", type_: Optional[str] = None) -> Entity:
    return Entity(id=name, kind=kind, type=type_ or kind, label=label)


def propagate(world: World) -> None:
    while True:
        fired_any = False
        for actor in world.characters():
            if actor.memes.get("stuck", 0) >= THRESHOLD and ("stuck_note", actor.id) not in world.fired:
                world.fired.add(("stuck_note", actor.id))
                world.say(f"{actor.id} frowned. The little plan still had a snag.")
                fired_any = True
            if actor.memes.get("surprised", 0) >= THRESHOLD and ("surprise_note", actor.id) not in world.fired:
                world.fired.add(("surprise_note", actor.id))
                world.say(f"{actor.id} blinked at the new clue.")
                fired_any = True
        if not fired_any:
            break


def tell(setting: Setting, task: Task, hero_kind: str, hero_name: str, helper_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind))
    helper_name = NAMES[helper_kind][0]
    if helper_name == hero_name:
        helper_name = NAMES[helper_kind][1]
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_kind))
    report = world.add(Entity(id="report", kind="thing", type="report", label="report", phrase="a careful little report"))

    world.facts.update(hero=hero, helper=helper, report=report, task=task, setting=setting)

    # Beginning
    world.say(
        f"{hero.id} the {hero.type} wanted to finish a report for the animal meeting. "
        f"{hero.pronoun().capitalize()} liked neat facts and tidy pages."
    )
    world.say(
        f"{helper.id} the {helper.type} came along because the two friends had promised to check the same spot twice, just to be sure."
    )

    # Repetition
    world.para()
    hero.memes["purpose"] = hero.memes.get("purpose", 0.0) + 1
    hero.memes["stuck"] = hero.memes.get("stuck", 0.0) + 1
    world.say(
        f"In {setting.place}, {hero.id} tried to {task.verb}. "
        f"{task.repetition.capitalize()} took a while, and the first try still looked messy."
    )
    world.say(f"{hero.id} tried again. Then {hero.id} tried one more time.")
    world.say(f"But {task.snag}.")

    propagate(world)

    # Surprise
    world.para()
    hero.memes["surprised"] = hero.memes.get("surprised", 0.0) + 1
    world.say(
        f"Just then, {task.surprise}. "
        f"{hero.id} stopped and stared. The new clue changed the whole day."
    )
    world.say(
        f"{helper.id} pointed at it and said, 'Let's use that.' "
        f"That was a surprise, but it made sense."
    )

    # Problem solving
    world.para()
    if task.id == "berries":
        world.say(
            f"{hero.id} and {helper.id} used the basket to sort the berries by color. "
            f"Red berries went in one side, purple berries in the other."
        )
    elif task.id == "birds":
        world.say(
            f"{hero.id} copied the tiny notes onto a leaf page while {helper.id} counted the birds again. "
            f"The feather helped the report stay true."
        )
    else:
        world.say(
            f"{hero.id} followed the frog to the hidden spring and filled the report with the real water source. "
            f"{helper.id} steadied the leaf page so it would not curl."
        )
    world.say(
        f"At last, {task.result}. {hero.id} smiled because the report was no longer stuck."
    )
    world.say(
        f"The two animals carried the report to the meeting, and everyone could see the careful answer at once."
    )

    report.prepared = True
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.facts["resolved"] = True
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task = f["hero"], f["helper"], f["task"]
    return [
        f"Write a short animal story where {hero.id} tries to make a report, repeats the task, then gets a surprise clue.",
        f"Tell a gentle story about {hero.id} and {helper.id} solving a report problem with patience and a smart fix.",
        f"Write a child-friendly animal story that includes the word report and shows repetition, surprise, and problem solving.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task = f["hero"], f["helper"], f["task"]
    return [
        QAItem(
            question=f"Who was trying to finish the report?",
            answer=f"{hero.id} the {hero.type} was trying to finish the report for the animal meeting.",
        ),
        QAItem(
            question=f"What made the story repeat for a while?",
            answer=f"{hero.id} kept trying to {task.verb} again and again, so the story repeated the same task before the fix worked.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {task.surprise}. That new clue changed how {hero.id} solved the problem.",
        ),
        QAItem(
            question=f"How did the animals solve the problem?",
            answer=f"{hero.id} and {helper.id} used a careful fix: they worked with the new clue instead of fighting it, and that helped the report get finished.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    task = world.facts["task"]
    out = [
        QAItem(
            question="What is a report?",
            answer="A report is a short set of facts or notes that tells other people what was found or done.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means doing or saying something again, which can make a story feel steady and easy to follow.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters think or do next.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty and choosing a smart way to fix it.",
        ),
    ]
    if "bird" in task.tags:
        out.append(QAItem(question="Why do birds sometimes move quickly?", answer="Birds move quickly because they are light and can flap away when they want to go somewhere else."))
    if "water" in task.tags:
        out.append(QAItem(question="Why do frogs like water?", answer="Frogs like water because it helps their skin stay damp and gives them a good place to hop and hide."))
    if "basket" in task.tags:
        out.append(QAItem(question="What is a basket for?", answer="A basket is used to carry or sort small things so they do not roll away."))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", task="berries", hero_kind="fox", hero_name="Fenn", helper_kind="rabbit"),
    StoryParams(setting="meadow", task="birds", hero_kind="owl", hero_name="Orla", helper_kind="squirrel"),
    StoryParams(setting="pond", task="water", hero_kind="frog", hero_name="Tiko", helper_kind="bear"),
]


def explain_rejection(setting: Setting, task: Task) -> str:
    return f"(No story: {task.verb} does not fit naturally at {setting.place}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for s in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, s))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("keyword", tid, task.keyword))
    for kind in ANIMALS:
        lines.append(asp.fact("animal", kind))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,T) :- setting(S), task(T), supports(S,X), keyword(T,X).
reasonable(S,T) :- setting(S), task(T), supports(S,X), tag(T,X).
tag(berries, basket).
tag(birds, bird).
tag(water, water).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if is_reasonable(setting, task):
                out.append((sid, tid))
    return out


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], params.hero_kind, params.hero_name, params.helper_kind)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        combos = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(combos)} reasonable setting/task combos:\n")
        for s, t in combos:
            print(f"  {s:10} {t}")
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
            header = f"### {p.hero_name}: {p.task} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
