#!/usr/bin/env python3
"""
A small standalone storyworld in the Animal Story style.

Seed tale:
---
A careful businessman named Bruno lived in a little town full of singing animals.
Bruno had an important exam at the market school, but he also needed to finish a
commission for the mayor: a shiny new sign painted with a rhyme.

Bruno wanted to skip the exam and rush to the commission, because the sign was
due that afternoon. But the rabbit teacher reminded him that the exam would help
him read the rhyme correctly. Bruno studied, took the exam, and then finished the
commission in time. The mayor loved the finished sign, and Bruno felt proud.

World model:
---
This world simulates one businessman-animal, one exam, one commission task, and
one rhyme-based solution. The tension is whether the character should ignore the
exam to finish the commission. The turn comes when the exam turns out to help
with the rhyme needed for the commission, so both obligations are met.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "businessman", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Exam:
    title: str
    subject: str
    rhyme: str
    difficulty: int = 1


@dataclass
class Commission:
    title: str
    client: str
    required_rhyme: str
    due: str
    reward: str


@dataclass
class StoryParams:
    name: str
    species: str
    role: str
    setting: str
    exam: str
    commission: str
    seed: Optional[int] = None


SPECIES = {
    "fox": {"names": ["Fenn", "Rufus", "Milo"], "role": "businessman"},
    "dog": {"names": ["Benny", "Arlo", "Ned"], "role": "businessman"},
    "bear": {"names": ["Bruno", "Hugo", "Orson"], "role": "businessman"},
    "rabbit": {"names": ["Poppy", "Tilly", "Mina"], "role": "businessman"},
}

SETTINGS = [
    "the busy town square",
    "the market school",
    "the little office by the bakery",
]

EXAMS = {
    "exam": Exam(
        title="market exam",
        subject="reading and counting",
        rhyme="tick-tock, shop and chalk",
        difficulty=1,
    ),
    "rhyme_exam": Exam(
        title="rhyme exam",
        subject="reading rhymes aloud",
        rhyme="shine and line, time and rhyme",
        difficulty=1,
    ),
}

COMMISSIONS = {
    "sign": Commission(
        title="a shiny sign",
        client="the mayor",
        required_rhyme="shine and line",
        due="that afternoon",
        reward="a gold star",
    ),
    "poster": Commission(
        title="a bright poster",
        client="the baker",
        required_rhyme="treat and neat",
        due="before supper",
        reward="a warm bun",
    ),
}


class World:
    def __init__(self, params: StoryParams, hero: Entity, exam: Exam, commission: Commission):
        self.params = params
        self.hero = hero
        self.exam = exam
        self.commission = commission
        self.entities = {"hero": hero}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def rhythm_line(word1: str, word2: str) -> str:
    return f"{word1} and {word2}"


def build_world(params: StoryParams) -> World:
    hero = Entity(
        id=params.name,
        kind="character",
        type=params.species,
        label=params.name,
        phrase=f"a {params.species} businessman",
        meters={"busy": 0.0, "skill": 1.0, "task": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "joy": 0.0},
    )
    return World(params, hero, EXAMS[params.exam], COMMISSIONS[params.commission])


def setup(world: World) -> None:
    h = world.hero
    world.say(
        f"In {world.params.setting}, there lived {h.phrase} named {h.id}."
    )
    world.say(
        f"{h.id} liked neat plans, tidy desks, and little rhymes that jingled like bells."
    )
    world.say(
        f"One day, {h.id} had to take the {world.exam.title} at {world.params.setting}."
    )
    world.say(
        f"At the same time, {h.id} also had a commission to finish: {world.commission.title} "
        f"for {world.commission.client}."
    )
    h.memes["worry"] += 1
    h.meters["busy"] += 1
    world.facts.update(hero=h, exam=world.exam, commission=world.commission)


def tension(world: World) -> None:
    h = world.hero
    world.para()
    world.say(
        f"{h.id} looked at the clock and sighed. "
        f"The commission was due {world.commission.due}, and the exam papers were stacked on the desk."
    )
    world.say(
        f"{h.id} wanted to hurry to the commission and skip the exam, because there was so much to do."
    )
    h.memes["worry"] += 1
    world.facts["skip_temptation"] = True


def turn(world: World) -> None:
    h = world.hero
    world.para()
    world.say(
        f"Then the rabbit teacher gave a gentle tip: the exam would help {h.pronoun('object')} read the rhyme on the sign."
    )
    world.say(
        f"The clue was simple: {rhythm_line('shine', 'line')} would fit the commission if {h.id} read the words carefully."
    )
    h.meters["skill"] += 1
    h.memes["worry"] = 0.0
    h.memes["hope"] = 1.0
    world.facts["helper"] = "teacher"
    world.facts["rhyme_help"] = True


def resolution(world: World) -> None:
    h = world.hero
    world.para()
    world.say(
        f"So {h.id} studied hard, took the exam, and read every rhyme aloud with a steady voice."
    )
    world.say(
        f"After that, {h.id} finished the commission for {world.commission.client} and painted the words "
        f"'{world.commission.required_rhyme}' onto {world.commission.title}."
    )
    h.meters["task"] += 1
    h.memes["joy"] += 1
    h.memes["pride"] += 1
    world.say(
        f"The {world.commission.client} smiled at the finished work, and {h.id} felt proud, calm, and bright."
    )
    world.say(
        f"That night, {h.id} went home with {world.commission.reward} and a happy rhyme in {h.pronoun('possessive')} mind."
    )
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    setup(world)
    tension(world)
    turn(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    h = world.hero
    e = world.exam
    c = world.commission
    return [
        f"Write an Animal Story about a {h.type} businessman who has an exam and a commission, and who uses a rhyme to solve both.",
        f"Tell a gentle story where {h.id} must take a {e.title} but also finish {c.title} for {c.client}.",
        f"Write a short child-friendly story with a hardworking animal, an exam, a commission, and a happy rhyme at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.hero
    c = world.commission
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {h.id}, a {h.type} businessman who tries to handle an exam and a commission.",
        ),
        QAItem(
            question=f"What was {h.id}'s commission?",
            answer=f"{h.id}'s commission was {c.title} for {c.client}.",
        ),
        QAItem(
            question=f"How did {h.id} solve the problem?",
            answer=(
                f"{h.id} took the exam first, learned the rhyme, and then finished the commission "
                f"without making a mistake."
            ),
        ),
        QAItem(
            question=f"Why did the exam matter?",
            answer=(
                f"The exam mattered because it helped {h.id} read the rhyme needed for the commission."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an exam?",
            answer="An exam is a set of questions or tasks that helps show what someone knows.",
        ),
        QAItem(
            question="What is a commission?",
            answer="A commission is a task someone is asked to do for another person, often for pay or praise.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, like shine and line.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
needs_exams(h) :- hero(h).
needs_commission(h) :- hero(h).
risk_conflict(h) :- needs_exams(h), needs_commission(h).
helpful_rhyme(h) :- risk_conflict(h), rhyme_ready(h), learns_exam(h).
resolved(h) :- helpful_rhyme(h).
#show needs_exams/1.
#show needs_commission/1.
#show risk_conflict/1.
#show helpful_rhyme/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hero", "h"),
        asp.fact("rhyme_ready", "h"),
        asp.fact("learns_exam", "h"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with an exam, a businessman, a commission, and a rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=sorted(SPECIES))
    ap.add_argument("--exam", choices=sorted(EXAMS))
    ap.add_argument("--commission", choices=sorted(COMMISSIONS))
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
    species = args.species or rng.choice(sorted(SPECIES))
    if species not in SPECIES:
        raise StoryError("Unknown species.")
    role = SPECIES[species]["role"]
    if role != "businessman":
        raise StoryError("This storyworld only supports a businessman animal.")
    name = args.name or rng.choice(SPECIES[species]["names"])
    place = args.place or rng.choice(SETTINGS)
    exam = args.exam or "exam"
    commission = args.commission or "sign"
    return StoryParams(name=name, species=species, role=role, setting=place, exam=exam, commission=commission)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    h = world.hero
    return (
        "--- world model state ---\n"
        f"  hero: {h.id} ({h.type}) meters={dict(h.meters)} memes={dict(h.memes)}\n"
        f"  exam: {world.exam.title}\n"
        f"  commission: {world.commission.title} for {world.commission.client}\n"
        f"  facts: {world.facts}"
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


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = {str(sym) for sym in model}
    expected = {"hero(h)", "rhyme_ready(h)", "learns_exam(h)", "needs_exams(h)", "needs_commission(h)", "risk_conflict(h)", "helpful_rhyme(h)", "resolved(h)"}
    if atoms == expected:
        print("OK: ASP rules match the Python story logic.")
        return 0
    print("MISMATCH between ASP and Python logic.")
    print("Atoms:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Bruno", species="bear", role="businessman", setting="the market school", exam="exam", commission="sign"),
            StoryParams(name="Fenn", species="fox", role="businessman", setting="the busy town square", exam="rhyme_exam", commission="poster"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
