#!/usr/bin/env python3
"""
storyworlds/worlds/exam_businessman_commission_rhyme_animal_story.py
===================================================================

A small, standalone storyworld about an animal child preparing for an exam,
a businessman who promises a commission, and a rhyming helper that turns
stress into a playful plan.

The world is intentionally tiny and constraint-checked:
- An exam can make a child worried.
- A businessman may offer a commission for help with a simple errand or job.
- A rhyme helper can calm the worry and guide the resolution.
- The story should feel like an Animal Story: concrete, gentle, and character-led.
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
class Character:
    id: str
    animal: str
    role: str
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def subject(self) -> str:
        return self.name


@dataclass
class World:
    characters: dict[str, Character] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


@dataclass
class StoryParams:
    hero_name: str
    hero_animal: str
    businessman_name: str
    helper_name: str
    exam_subject: str
    commission_task: str
    rhyme_word: str
    seed: Optional[int] = None


HEROES = [
    ("Milo", "mouse"),
    ("Nina", "rabbit"),
    ("Pip", "piglet"),
    ("Tess", "turtle"),
    ("Bram", "bear cub"),
    ("Luna", "fox kit"),
]

BUSINESSMEN = ["Mr. Button", "Mr. Brick", "Mr. Hobb", "Mr. Vale"]
HELPERS = ["Bee", "Crow", "Otter", "Moth"]
SUBJECTS = ["spelling", "numbers", "reading", "shapes"]
TASKS = ["carry papers", "sort buttons", "deliver a note", "count coins"]
RHYMES = ["light", "bright", "near", "clear", "play", "day"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story: exam, businessman, commission, rhyme.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-animal")
    ap.add_argument("--businessman-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--exam-subject", choices=SUBJECTS)
    ap.add_argument("--commission-task", choices=TASKS)
    ap.add_argument("--rhyme-word", choices=RHYMES)
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
    hero_name, hero_animal = args.hero_name, args.hero_animal
    if hero_name and not hero_animal:
        raise StoryError("If --hero-name is set, --hero-animal is also required.")
    if hero_animal and not hero_name:
        raise StoryError("If --hero-animal is set, --hero-name is also required.")
    if hero_animal and hero_animal not in {a for _, a in HEROES}:
        raise StoryError("Unknown hero animal.")
    if args.commission_task == "deliver a note" and args.exam_subject == "shapes":
        pass

    if hero_name is None:
        hero_name, hero_animal = rng.choice(HEROES)
    businessman_name = args.businessman_name or rng.choice(BUSINESSMEN)
    helper_name = args.helper_name or rng.choice(HELPERS)
    exam_subject = args.exam_subject or rng.choice(SUBJECTS)
    commission_task = args.commission_task or rng.choice(TASKS)
    rhyme_word = args.rhyme_word or rng.choice(RHYMES)

    if commission_task == "count coins" and exam_subject == "numbers":
        # valid, but if user pins this combo, the businessman can honestly offer help
        pass

    return StoryParams(
        hero_name=hero_name,
        hero_animal=hero_animal,
        businessman_name=businessman_name,
        helper_name=helper_name,
        exam_subject=exam_subject,
        commission_task=commission_task,
        rhyme_word=rhyme_word,
    )


def build_world(params: StoryParams) -> World:
    w = World()
    hero = Character("hero", params.hero_animal, "student", params.hero_name)
    boss = Character("businessman", "badger", "businessman", params.businessman_name)
    helper = Character("helper", "bird", "friend", params.helper_name)
    w.characters = {"hero": hero, "businessman": boss, "helper": helper}
    return w


def simulate(params: StoryParams) -> World:
    w = build_world(params)
    hero = w.characters["hero"]
    boss = w.characters["businessman"]
    helper = w.characters["helper"]

    hero.memes["worry"] = 1
    hero.memes["hope"] = 0
    boss.memes["pressure"] = 1

    w.say(
        f"{hero.name} the {hero.animal} had an exam in {params.exam_subject} at school."
    )
    w.say(
        f"Before class, {hero.name} met {boss.name}, a busy businessman with a shiny hat."
    )
    w.say(
        f"{boss.name} needed someone to {params.commission_task}, and promised a small commission."
    )
    w.say(
        f"{hero.name} wanted the commission, but the exam made {hero.name} feel small and shy."
    )

    hero.memes["worry"] += 1
    w.facts["exam_subject"] = params.exam_subject
    w.facts["commission_task"] = params.commission_task
    w.facts["rhyme_word"] = params.rhyme_word

    if params.rhyme_word in {"light", "bright", "clear"}:
        helper_line = (
            f"{helper.name} the little bird chirped a rhyme: "
            f'"Keep your head high and your heart so light, '
            f"and your busy day will feel bright.\""
        )
    else:
        helper_line = (
            f"{helper.name} the little bird chirped a rhyme: "
            f'"One small step and one good plan will carry you through the day.\"'
        )
    w.say(helper_line)

    hero.memes["worry"] = max(0, hero.memes["worry"] - 1)
    hero.memes["hope"] += 1

    if params.exam_subject == "numbers":
        exam_help = "counting carefully"
    elif params.exam_subject == "spelling":
        exam_help = "saying each word slowly"
    elif params.exam_subject == "reading":
        exam_help = "moving from line to line"
    else:
        exam_help = "looking for the right shapes"

    w.say(
        f"{hero.name} took a deep breath, used the rhyme as a guide, and studied by {exam_help}."
    )
    w.say(
        f"After the exam, {hero.name} went back to {boss.name} and finished the commission."
    )
    w.say(
        f"The businessman smiled, paid the small commission, and said the work was done well."
    )
    w.say(
        f"{hero.name} smiled too, because the exam was over and the day felt {params.rhyme_word}."
    )

    w.facts["resolved"] = True
    w.facts["hero"] = hero
    w.facts["businessman"] = boss
    w.facts["helper"] = helper
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Animal Story about an exam, a businessman, and a commission, with a gentle rhyme.',
        f"Tell a story where {f['hero'].name} the {f['hero'].animal} worries about a {f['exam_subject']} exam and still helps a businessman.",
        f"Create a child-friendly story that includes the word '{f['rhyme_word']}' and ends with a happy commission being earned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    boss = f["businessman"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Why was {hero.name} worried at the start of the story?",
            answer=f"{hero.name} was worried because {hero.name} had an exam in {f['exam_subject']} and wanted to do well.",
        ),
        QAItem(
            question=f"What did {boss.name} want {hero.name} to do for a commission?",
            answer=f"{boss.name} wanted {hero.name} to {f['commission_task']}.",
        ),
        QAItem(
            question=f"Who helped {hero.name} feel braver?",
            answer=f"{helper.name} the bird helped by sharing a rhyme and calming {hero.name} down.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The exam was finished, the commission was done, and {hero.name} felt happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an exam?", answer="An exam is a school test that asks you to show what you know."),
        QAItem(question="What is a businessman?", answer="A businessman is a person who works with jobs, plans, and money."),
        QAItem(question="What is a commission?", answer="A commission is money paid for doing a job or helping with a task."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a pair of words or lines that sound alike at the end."),
    ]


ASP_RULES = r"""
exam_worry(H) :- hero(H), has_exam(H).
need_help(H) :- exam_worry(H), business_offer(B), commission_task(B,T), can_help(H,T).
happy_end(H) :- need_help(H), rhyme_help(H).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("business_offer", "businessman"),
        asp.fact("has_exam", "hero"),
        asp.fact("commission_task", "businessman", "task"),
        asp.fact("rhyme_help", "hero"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Minimal parity check: program should be solvable and show the intended atom.
    import asp
    model = asp.one_model(asp_program("#show happy_end/1."))
    atoms = asp.atoms(model, "happy_end")
    if atoms:
        print("OK: ASP gate produced a happy ending atom.")
        return 0
    print("MISMATCH: ASP gate did not produce the expected atom.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if k not in {"hero", "businessman", "helper"}:
                print(f"{k}: {v}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show happy_end/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/1."))
        print(asp.atoms(model, "happy_end"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i in range(min(args.n, 6)):
            p = StoryParams(
                hero_name=HEROES[i][0],
                hero_animal=HEROES[i][1],
                businessman_name=BUSINESSMEN[i % len(BUSINESSMEN)],
                helper_name=HELPERS[i % len(HELPERS)],
                exam_subject=SUBJECTS[i % len(SUBJECTS)],
                commission_task=TASKS[i % len(TASKS)],
                rhyme_word=RHYMES[i % len(RHYMES)],
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
