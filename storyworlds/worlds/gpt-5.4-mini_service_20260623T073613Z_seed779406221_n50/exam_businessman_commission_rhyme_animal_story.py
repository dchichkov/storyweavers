#!/usr/bin/env python3
"""
storyworlds/worlds/exam_businessman_commission_rhyme_animal_story.py
====================================================================

A small animal-story world about an exam, a businessman, and a commission.

Seed tale:
---
A little rabbit named Pip had an important exam at school. In town, a busy
businessman named Mr. Finch needed a poster for his shop and promised a
commission to whoever could make it. Pip worried because the exam and the
commission were both on the same day.

Pip's friend Momo the fox saw the problem and suggested a rhyme to help Pip
remember the answers. Later, Pip gave the businessman a neat drawing for the
commission, then went to the exam calm and ready. The rhyme helped, and Pip
passed. The businessman liked the work and paid the commission with a smile.
---

The world is built from that premise:
- physical meters: distance, papers, coins, time, travel
- emotional memes: worry, confidence, pride, relief, kindness
- a forward causal turn: fear of failing the exam versus earning the commission
- a resolution: a rhyme-based mnemonic and a timed schedule make both possible
"""

from __future__ import annotations

import argparse
import copy
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    ridden_by: Optional[str] = None
    note: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "bunny", "fox", "mouse", "cat", "dog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"man", "businessman"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Exam:
    subject: str
    place: str
    need: str
    rhyme_hint: str


@dataclass
class Commission:
    item: str
    client_label: str
    payment: str
    due: str


@dataclass
class Helper:
    name: str
    type: str
    rhyme: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    businessman_name: str
    businessman_type: str
    helper_name: str
    helper_type: str
    exam_subject: str
    commission_item: str
    place: str
    seed: Optional[int] = None


HEROES = [
    ("Pip", "rabbit"),
    ("Milo", "mouse"),
    ("Luna", "fox"),
    ("Nori", "cat"),
    ("Toby", "dog"),
]
BUSINESS = [
    ("Mr. Finch", "businessman"),
    ("Mr. Tallow", "businessman"),
    ("Mr. Brisk", "businessman"),
]
HELPERS = [
    ("Momo", "fox"),
    ("Nina", "cat"),
    ("Bea", "mouse"),
]
SUBJECTS = ["math", "reading", "spelling", "nature"]
ITEMS = [("poster", "poster"), ("sign", "shop sign"), ("label", "bright label")]
PLACES = ["school", "the little shop", "the market hall"]


def rhyme_line(word: str) -> str:
    return {
        "math": "In a flash, do the math; take the calm path.",
        "reading": "Read with glee, then you will see.",
        "spelling": "Spell it right, like stars at night.",
        "nature": "Look and learn, then take your turn.",
    }.get(word, "Take a breath, then do your best.")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, p) for s in SUBJECTS for c in [i[0] for i in ITEMS] for p in PLACES]


def build_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    boss = w.add(Entity(id=params.businessman_name, kind="character", type=params.businessman_type, label=params.businessman_name))
    helper = w.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    exam = Exam(subject=params.exam_subject, place=params.place, need="a calm mind", rhyme_hint=rhyme_line(params.exam_subject))
    commission = Commission(item=params.commission_item, client_label=boss.label, payment="a shiny coin purse", due="the same day")
    w.facts.update(hero=hero, boss=boss, helper=helper, exam=exam, commission=commission)

    hero.memes["worry"] = 1.0
    boss.memes["expectation"] = 1.0
    helper.memes["kindness"] = 1.0

    hero.meters["time"] = 1.0
    boss.meters["time"] = 1.0
    helper.meters["time"] = 1.0

    w.say(f"{hero.id} was a little {hero.type} who had an exam at {exam.place}.")
    w.say(f"At the same time, {boss.label} the businessman wanted a {commission.item} and offered a commission.")
    w.say(f"{helper.id} saw the tangle and said, “{exam.rhyme_hint}”")
    w.para()
    w.say(f"{hero.id} listened to the rhyme, and the worry in {hero.pronoun('possessive')} chest grew small.")
    w.say(f"{hero.id} made the {commission.item} neatly, then hurried to the exam with steady steps.")
    hero.meters["finished_art"] = 1.0
    hero.meters["exam_ready"] = 1.0
    hero.memes["confidence"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = 1.0
    boss.memes["pleasure"] = 1.0
    boss.meters["paid"] = 1.0
    w.para()
    w.say(f"{boss.label} smiled, paid the commission, and said the {commission.item} was just right.")
    w.say(f"Then {hero.id} went in for the exam and did well, because the rhyme kept the thoughts in line.")
    w.say(f"By the end of the day, {hero.id} had both a passed exam and a happy commission story to tell.")
    w.facts["outcome"] = "both"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ex: Exam = f["exam"]
    com: Commission = f["commission"]
    hero = f["hero"]
    boss = f["boss"]
    helper = f["helper"]
    return [
        f'Write a short animal story for a child about {hero.id}, an exam, and a commission from {boss.label}. Include a rhyme.',
        f"Tell a gentle story where {hero.id} has to study for {ex.subject} at {ex.place} while making a {com.item} for {boss.label}.",
        f'Write an animal story that uses the word "commission" and ends with a helpful rhyme and a calm exam.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    boss = f["boss"]
    helper = f["helper"]
    ex: Exam = f["exam"]
    com: Commission = f["commission"]
    return [
        QAItem(
            question=f"What two things did {hero.id} have to do on the same day?",
            answer=f"{hero.id} had an exam at {ex.place} and also had to finish a {com.item} for {boss.label}. That was hard, so the day needed a careful plan."
        ),
        QAItem(
            question=f"Who helped {hero.id} remember what to do?",
            answer=f"{helper.id} helped by saying a rhyme: “{ex.rhyme_hint}” It made the work feel lighter and helped {hero.id} stay calm."
        ),
        QAItem(
            question=f"What did {boss.label} want from {hero.id}?",
            answer=f"{boss.label} wanted a {com.item} and offered a commission. {hero.id} made it neatly before going to the exam."
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} finished the {com.item}, took the exam, and did well. The rhyme helped turn a busy day into a successful one."
        ),
    ]


WORLD_KNOWLEDGE = {
    "exam": [("What is an exam?", "An exam is a set of questions or tasks that helps show what you know.")],
    "commission": [("What is a commission?", "A commission is a job someone asks you to do, often for payment.")],
    "businessman": [("What does a businessman do?", "A businessman sells goods or services and helps run a shop or company.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like light and night.")],
    "rabbit": [("What is a rabbit?", "A rabbit is a small animal with long ears that likes to hop.")],
    "fox": [("What is a fox?", "A fox is a clever wild animal with a bushy tail.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question=q, answer=a)
        for key in ["exam", "commission", "businessman", "rhyme", "rabbit", "fox"]
        if key in WORLD_KNOWLEDGE
        for q, a in WORLD_KNOWLEDGE[key]
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: exam, businessman, commission, and rhyme.")
    ap.add_argument("--hero-name", choices=[n for n, _ in HEROES])
    ap.add_argument("--hero-type", choices=sorted({t for _, t in HEROES}))
    ap.add_argument("--businessman-name", choices=[n for n, _ in BUSINESS])
    ap.add_argument("--businessman-type", choices=sorted({t for _, t in BUSINESS}))
    ap.add_argument("--helper-name", choices=[n for n, _ in HELPERS])
    ap.add_argument("--helper-type", choices=sorted({t for _, t in HELPERS}))
    ap.add_argument("--exam-subject", choices=SUBJECTS)
    ap.add_argument("--commission-item", choices=[x for x, _ in ITEMS])
    ap.add_argument("--place", choices=PLACES)
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
    hero_name, hero_type = args.hero_name, args.hero_type
    if not hero_name or not hero_type:
        hero_name, hero_type = rng.choice(HEROES)
    biz_name, biz_type = args.businessman_name, args.businessman_type
    if not biz_name or not biz_type:
        biz_name, biz_type = rng.choice(BUSINESS)
    help_name, help_type = args.helper_name, args.helper_type
    if not help_name or not help_type:
        help_name, help_type = rng.choice(HELPERS)
    ex = args.exam_subject or rng.choice(SUBJECTS)
    item = args.commission_item or rng.choice([x for x, _ in ITEMS])[0]
    place = args.place or rng.choice(PLACES)
    return StoryParams(hero_name, hero_type, biz_name, biz_type, help_name, help_type, ex, item, place)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
hero(H) :- hero_name(H).
businessman(B) :- businessman_name(B).
helper(X) :- helper_name(X).
rhyme_ok(E) :- exam(E), rhyme(E).
commission_job(C) :- commission(C).
story_ready(H,B,X) :- hero(H), businessman(B), helper(X).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for n, t in HEROES:
        lines.append(asp.fact("hero_name", n))
        lines.append(asp.fact("hero_type", t))
    for n, t in BUSINESS:
        lines.append(asp.fact("businessman_name", n))
        lines.append(asp.fact("businessman_type", t))
    for n, t in HELPERS:
        lines.append(asp.fact("helper_name", n))
        lines.append(asp.fact("helper_type", t))
    for s in SUBJECTS:
        lines.append(asp.fact("exam", s))
        lines.append(asp.fact("rhyme", s))
    for item, _ in ITEMS:
        lines.append(asp.fact("commission", item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ready/3."))
    atoms = set(asp.atoms(model, "story_ready"))
    expected = {(h[0], b[0], x[0]) for h in [(n,) for n, _ in HEROES] for b in [(n,) for n, _ in BUSINESS] for x in [(n,) for n, _ in HELPERS]}
    if atoms != expected:
        print("MISMATCH")
        return 1
    print("OK: ASP facts and Python registry agree.")
    return 0


CURATED = [
    StoryParams("Pip", "rabbit", "Mr. Finch", "businessman", "Momo", "fox", "math", "poster", "school"),
    StoryParams("Luna", "fox", "Mr. Brisk", "businessman", "Nina", "cat", "reading", "sign", "the little shop"),
    StoryParams("Toby", "dog", "Mr. Tallow", "businessman", "Bea", "mouse", "spelling", "label", "the market hall"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ready/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show story_ready/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
