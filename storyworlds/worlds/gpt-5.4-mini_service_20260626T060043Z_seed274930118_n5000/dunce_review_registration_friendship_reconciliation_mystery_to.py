#!/usr/bin/env python3
"""
A small adventure storyworld about a mistaken "dunce" label, a careful review,
a registration list, friendship, reconciliation, and a mystery that needs to be
solved.

The seed premise:
- A child is worried about being called a dunce during a review.
- A registration task is incomplete or mixed up.
- A friend helps uncover the real mystery.
- The misunderstanding is repaired through reconciliation.

This script keeps the world tiny, state-driven, and child-facing.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def they(self) -> str:
        return "them" if self.type in {"girl", "boy"} else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    tension: str
    clue: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    owner_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0


SETTINGS = {
    "schoolyard": Setting(
        place="the schoolyard",
        detail="The schoolyard was bright, with a notice board near the gate.",
        affords={"review", "registration"},
    ),
    "library": Setting(
        place="the library",
        detail="The library was quiet, with a long table full of papers.",
        affords={"review", "registration"},
    ),
    "clubroom": Setting(
        place="the clubroom",
        detail="The clubroom smelled like crayons and paper glue.",
        affords={"review", "registration"},
    ),
}

TASKS = {
    "review": Task(
        id="review",
        verb="review the list",
        gerund="reviewing the list",
        tension="looked over the papers",
        clue="the pages were out of order",
        keyword="review",
        tags={"review", "mystery"},
    ),
    "registration": Task(
        id="registration",
        verb="check the registration",
        gerund="checking the registration",
        tension="count the names",
        clue="one line was missing a name",
        keyword="registration",
        tags={"registration", "mystery"},
    ),
    "mystery": Task(
        id="mystery",
        verb="solve the mystery",
        gerund="solving the mystery",
        tension="follow the clues",
        clue="a pencil mark pointed to the wrong page",
        keyword="mystery",
        tags={"mystery"},
    ),
}

PRIZES = {
    "badge": Prize(
        label="badge",
        phrase="a bright club badge",
        region="pocket",
        owner_word="badge",
        tags={"registration"},
    ),
    "folder": Prize(
        label="folder",
        phrase="a blue paper folder",
        region="hand",
        owner_word="folder",
        tags={"review", "mystery"},
    ),
    "sheet": Prize(
        label="sheet",
        phrase="a sign-up sheet",
        region="hand",
        owner_word="sheet",
        tags={"registration"},
    ),
}

NAMES = ["Mina", "Toby", "Lena", "Owen", "Ivy", "Eli", "Nora", "Jude"]
TRAITS = ["brave", "curious", "careful", "kind", "steady", "lively"]


@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    name: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    prize = PRIZES[params.prize]
    if params.task not in setting.affords:
        raise StoryError("That setting cannot host this task.")
    if task.id == "review" and prize.label == "badge":
        return
    if task.id == "registration" and prize.label in {"badge", "sheet"}:
        return
    if task.id == "mystery" and prize.label in {"folder", "sheet"}:
        return
    raise StoryError("This story needs a prize that can plausibly be involved in the task.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: friendship, reconciliation, mystery, and registration.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for p in PRIZES:
                try:
                    reasonableness_gate(StoryParams(s, t, p, "A", "B", "kind"))
                except StoryError:
                    continue
                combos.append((s, t, p))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, prize = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        task=task,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice([n for n in NAMES if n != (args.name or "")]),
        trait=args.trait or rng.choice(TRAITS),
    )


def _do_story(world: World, hero: Entity, friend: Entity, task: Task, prize: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait_word', 'kind')} child who loved adventure.")
    world.say(f"One day, {hero.id} and {friend.id} went to {world.setting.place}.")
    world.say(world.setting.detail)
    world.say(f"They needed to {task.verb}, but {task.clue}.")

    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    world.say(f"Then someone muttered that {hero.id} was a dunce, and the word stung like a sharp pebble.")

    world.para()
    world.say(f"{friend.id} did not laugh. {friend.id} bent over the papers and pointed to a clue.")
    world.say(f"It turned out {task.clue}, which meant the mistake was in the registration, not in {hero.id}.")
    world.say(f"Together they fixed the {prize.label} and checked the list again.")
    world.say(f"{friend.id} said, \"You are not a dunce. You found the real problem.\"")

    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1

    world.para()
    world.say(f"{hero.id} smiled and {friend.id} smiled back. The two friends finished the {task.keyword} work side by side.")
    world.say(f"At the end, the {prize.label} was in order, the names were clear, and the mystery was solved.")
    world.say(f"{hero.id} walked home feeling light, with {friend.id} beside them and the paper work safely done.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    prize_cfg = PRIZES[params.prize]
    world = World(setting=setting)

    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="child"))
    prize = world.add(Entity(id="prize", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    hero.memes["trait_word"] = 0.0
    hero.memes["trait_word"] = 1.0

    _do_story(world, hero, friend, task, prize)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        task=task,
        setting=setting,
        params=params,
        reconciled=True,
    )

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
    hero = f["hero"]
    task = f["task"]
    return [
        f'Write an adventure story for a young child about {hero.id}, friendship, and {task.keyword}.',
        f'Tell a gentle story where {hero.id} is called a dunce during a {task.keyword} task and a friend helps solve the mistake.',
        f'Write a short story about a registration problem, a hidden clue, and reconciliation between friends.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    task = f["task"]
    prize = f["prize"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, who went on a small adventure with {friend.id}.",
        ),
        QAItem(
            question=f"What problem did they work on at {setting.place}?",
            answer=f"They worked on {task.gerund} and discovered that the real problem was a mistake in the registration work.",
        ),
        QAItem(
            question=f"Why did the word dunce stop hurting by the end?",
            answer=f"It stopped hurting because {friend.id} helped solve the mystery, proved the mistake was not {hero.id}'s fault, and they reconciled.",
        ),
        QAItem(
            question=f"What was finally fixed?",
            answer=f"They fixed the {prize.label}, got the names in order, and finished the task together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or puzzle where you do not know the answer right away.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after hurt feelings or a disagreement.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind.",
        ),
        QAItem(
            question="What is registration?",
            answer="Registration is writing names down so people can join, enter, or be counted.",
        ),
        QAItem(
            question="What does a review do?",
            answer="A review means looking carefully over something to check for mistakes or to understand it better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_task(T) :- activity(T).
valid_prize(P) :- prize(P).

compatible(S,T,P) :- valid_setting(S), valid_task(T), valid_prize(P),
                     affords(S,T), works(T,P).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("activity", tid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for t in TASKS.values():
        for p in PRIZES.values():
            if t.id == "review" and p.label == "folder":
                lines.append(asp.fact("works", t.id, p.label))
            if t.id == "review" and p.label == "badge":
                lines.append(asp.fact("works", t.id, p.label))
            if t.id == "registration" and p.label in {"badge", "sheet"}:
                lines.append(asp.fact("works", t.id, p.label))
            if t.id == "mystery" and p.label in {"folder", "sheet"}:
                lines.append(asp.fact("works", t.id, p.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("schoolyard", "review", "folder", "Mina", "Owen", "curious"),
        StoryParams("library", "registration", "sheet", "Toby", "Lena", "brave"),
        StoryParams("clubroom", "mystery", "badge", "Ivy", "Jude", "careful"),
    ]


CURATED = build_curated()


def resolve_story_specific(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, t, p = rng.choice(sorted(combos))
    return StoryParams(
        setting=s,
        task=t,
        prize=p,
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice([n for n in NAMES if n != (args.name or "")]),
        trait=args.trait or rng.choice(TRAITS),
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        for s, t, p in triples:
            print(f"{s:12} {t:12} {p}")
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
            params = resolve_story_specific(args, random.Random(seed))
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
            header = f"### {p.name}: {p.task} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
