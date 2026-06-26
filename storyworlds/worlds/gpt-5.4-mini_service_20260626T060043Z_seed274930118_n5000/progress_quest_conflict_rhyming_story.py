#!/usr/bin/env python3
"""
storyworlds/worlds/progress_quest_conflict_rhyming_story.py
===========================================================

A small story world about a quest that makes steady progress, meets a conflict,
and resolves with a kind, child-facing ending in a rhyming-story style.
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
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Quest:
    id: str
    goal: str
    gerund: str
    step: str
    progress_gain: float
    conflict: str
    obstacle: str
    fix: str
    rhyme_a: str
    rhyme_b: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Setting:
    place: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting("the garden", "The garden had a small stone path and a shy little gate.", {"green"}),
    "hill": Setting("the hill", "The hill was windy, with a narrow path that zigzagged up.", {"wind"}),
    "harbor": Setting("the harbor", "The harbor had bright ropes, round shells, and boats that bobbed.", {"water"}),
    "library": Setting("the library", "The library was quiet, with tall shelves and a soft red rug.", {"quiet"}),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="find the little lantern",
        gerund="finding the little lantern",
        step="follow the glow",
        progress_gain=1.0,
        conflict="a dark puddle hid the way",
        obstacle="the puddle was wide and slick",
        fix="they used a dry board as a bridge",
        rhyme_a="The path was dim, but not too far,",
        rhyme_b="They followed the glow like a tiny star.",
        tags={"light", "night"},
    ),
    "puzzle": Quest(
        id="puzzle",
        goal="solve the picture puzzle",
        gerund="solving the picture puzzle",
        step="match the shapes",
        progress_gain=1.0,
        conflict="two pieces would not fit",
        obstacle="the pieces were stuck with a stubborn twist",
        fix="they turned the pieces and tried again",
        rhyme_a="A piece would sulk and a piece would pout,",
        rhyme_b="But turning them gently helped them out.",
        tags={"brain", "quiet"},
    ),
    "bridge": Quest(
        id="bridge",
        goal="build the little bridge",
        gerund="building the little bridge",
        step="stack the sticks",
        progress_gain=1.0,
        conflict="one stick kept slipping away",
        obstacle="the sticks slid fast on the smooth ground",
        fix="they tied the sticks with a ribbon knot",
        rhyme_a="The sticks went slide and the sticks went swish,",
        rhyme_b="Then a ribbon knot made a sturdy wish.",
        tags={"craft", "water"},
    ),
}


GENDERS = ["girl", "boy"]
HELPERS = ["sister", "brother", "friend", "cousin"]
NAMES_GIRL = ["Maya", "Lina", "Nora", "Tia", "Zoe", "Ella"]
NAMES_BOY = ["Ben", "Leo", "Finn", "Noah", "Theo", "Max"]


class World:
    def __init__(self, setting: Setting, quest: Quest) -> None:
        self.setting = setting
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    if hero.meters.get("progress", 0) >= THRESHOLD and "progress" not in world.fired:
        world.fired.add("progress")
        out.append("Step by step, the quest made progress.")
    return out


def _conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    if hero.memes.get("worry", 0) >= THRESHOLD and "conflict" not in world.fired:
        world.fired.add("conflict")
        out.append("A small conflict curled up like a cloud.")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    all_lines: list[str] = []
    while changed:
        changed = False
        for rule in (_progress, _conflict):
            lines = rule(world)
            if lines:
                changed = True
                all_lines.extend(lines)
    if narrate:
        for line in all_lines:
            world.say(line)


def build_story(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    quest = world.quest

    world.say(f"Once there was {hero.label}, who loved a quest with a little beat.")
    world.say(f"{hero.pronoun().capitalize()} wanted {quest.gerund}, neat and sweet.")
    world.say(f"With {helper.label} along, {hero.pronoun('possessive')} heart felt bright and fleet.")
    world.say(f"{quest.rhyme_a} {quest.rhyme_b}")

    world.para()
    world.say(f"At {world.setting.place}, {world.setting.detail}")
    world.say(f"So {hero.label} began to {quest.step}, one careful step at a time.")
    hero.meters["progress"] = hero.meters.get("progress", 0) + quest.progress_gain
    propagate(world)

    world.para()
    hero.memes["worry"] = 1.0
    world.say(f"But then came trouble: {quest.conflict}.")
    world.say(f"{quest.obstacle}, and the path did not seem kind.")
    propagate(world)

    world.para()
    world.say(f"{helper.label} smiled and said, '{quest.fix}.'")
    hero.memes["worry"] = 0.0
    hero.meters["progress"] += 1.0
    propagate(world)

    world.para()
    world.say(
        f"In the end, {hero.label} finished the quest and felt proud and free. "
        f"The little prize was found, and the cloudy conflict drifted away."
    )
    world.say(
        f"{hero.label} and {helper.label} went home with happy feet, "
        f"their rhyme soft as a song."
    )
    world.facts.update(hero=hero, helper=helper, quest=quest, setting=world.setting)


def tell(setting_key: str, quest_key: str, name: str, gender: str, helper: str) -> World:
    setting = SETTINGS[setting_key]
    quest = QUESTS[quest_key]
    world = World(setting, quest)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    other = world.add(Entity(id="helper", kind="character", type=helper, label=f"the {helper}"))
    world.facts["hero_name"] = name
    world.facts["helper_name"] = helper
    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about a child named {f["hero_name"]} on a quest at {world.setting.place}.',
        f"Tell a gentle story where {f['hero_name']} makes progress, meets a conflict, and finishes a quest with {f['helper_name']}.",
        f"Write a child-friendly quest story in a rhyming style, with a problem that gets solved kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was {hero.label} trying to do?",
            answer=f"{hero.label} was trying to {quest.gerund}.",
        ),
        QAItem(
            question=f"Who helped {hero.label} on the quest?",
            answer=f"{helper.label} helped {hero.label} on the quest.",
        ),
        QAItem(
            question="What problem caused the conflict?",
            answer=f"The conflict happened because {quest.conflict}.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"They solved it when {quest.fix}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone tries to reach a goal.",
        ),
        QAItem(
            question="What does progress mean?",
            answer="Progress means moving closer to a goal, little by little.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem or disagreement that makes things harder for a while.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
progress(1).
quest(quest).
conflict(conflict) :- worry(hero).
resolved :- progress(1), not conflict(conflict).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", sid)
        for sid in SETTINGS
    ]
    lines += [asp.fact("quest", qid) for qid in QUESTS]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming quest story world with progress and conflict.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, quest=quest, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.quest, params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, label={e.label}, meters={e.meters}, memes={e.memes}")
    lines.append(f"setting={world.setting.place}")
    lines.append(f"quest={world.quest.id}")
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


def _asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show setting/1.\n"))
    if model is None:
        print("ASP model missing.")
        return 1
    print("OK: ASP program solved.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest/1.\n#show setting/1.\n"))
        return
    if args.verify:
        sys.exit(_asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in sorted(SETTINGS):
            for quest in sorted(QUESTS):
                params = StoryParams(
                    setting=setting,
                    quest=quest,
                    name="Mia",
                    gender="girl",
                    helper="friend",
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
