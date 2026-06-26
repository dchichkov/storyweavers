#!/usr/bin/env python3
"""
A standalone storyworld: a little faker-author, a stain, a lesson learned,
a transformation, and a kinder ending, told in a rhyming story style.

This world models a child who tries to pass off a stained page as perfect, then
learns honesty and kindness when the truth helps more than the trick.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the little writing nook"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    mess: str
    stain_word: str
    emotional_tension: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    label: str
    action: str
    result: str
    helper: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "nook": Setting(place="the little writing nook", indoors=True, affords={"write", "erase", "tell_truth"}),
    "table": Setting(place="the craft table", indoors=True, affords={"write", "erase", "tell_truth"}),
}

PROBLEMS = {
    "stain": Problem(
        id="stain",
        verb="smudge the page",
        gerund="smudging the page",
        mess="stained",
        stain_word="stain",
        emotional_tension="embarrassment",
        tags={"stain", "mess", "lesson"},
    ),
    "ink": Problem(
        id="ink",
        verb="spill ink on the note",
        gerund="spilling ink on the note",
        mess="inked",
        stain_word="ink stain",
        emotional_tension="worry",
        tags={"stain", "ink", "lesson"},
    ),
}

LESSONS = {
    "kindness": Lesson(
        id="kindness",
        label="kindness",
        action="ask for help and tell the truth",
        result="the mess could be fixed",
        helper="a kind friend",
        tags={"kindness", "lesson", "transformation"},
    ),
    "truth": Lesson(
        id="truth",
        label="truth",
        action="be honest about the stain",
        result="the page could start fresh",
        helper="a gentle adult",
        tags={"lesson", "transformation"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max"]
TRAITS = ["curious", "shy", "bright", "gentle", "spirited"]


@dataclass
class StoryParams:
    place: str
    problem: str
    lesson: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
problem_at_risk(P) :- problem(P).
lesson_valid(L) :- lesson(L).
story_ok(Place, Prob, Les) :- setting(Place), problem(Prob), lesson(Les).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for prob in PROBLEMS:
            for les in LESSONS:
                combos.append((place, prob, les))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about a faker, a stain, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    lesson = args.lesson or rng.choice(list(LESSONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, lesson=lesson, name=name, gender=gender, trait=trait)


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait, "faker"],
        meters={"mess": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "kindness": 0.0, "honesty": 0.0, "lesson_learned": 0.0, "transformation": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type="mother",
        label="a gentle adult",
        meters={"mess": 0.0},
        memes={"care": 1.0},
    ))
    problem = PROBLEMS[params.problem]
    lesson = LESSONS[params.lesson]
    world.facts.update(hero=hero, adult=adult, problem=problem, lesson=lesson)

    world.say(f"{hero.id} was a little faker with a pen and a grin,")
    world.say(f"who loved to make rhymes and make stories begin.")
    world.say(f"But one small day in {world.setting.place}, oh what a surprise,")
    world.say(f"a {problem.stain_word} slipped in and spotted the page with its lies.")

    world.para()
    world.say(f"{hero.id} had tried to {problem.verb}, quick as a wink,")
    world.say(f"then hid the {problem.stain_word} with a cover-up trick.")
    hero.meters["mess"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(f"The more the faker pretended, the heavier it grew;")
    world.say(f"the stain on the page made the worry come through.")

    world.para()
    world.say(f"Then {adult.label} said, 'Sweet one, let's stop for a bit,")
    world.say(f"if we tell the truth kindly, we can still fix it.'")
    world.say(f"'A lesson learned shines brighter than glue and than paste;")
    world.say(f"kindness and honesty save time in a haste.'")
    hero.memes["honesty"] += 1.0
    hero.memes["kindness"] += 1.0
    hero.memes["transformation"] += 1.0
    hero.memes["lesson_learned"] += 1.0

    world.para()
    world.say(f"{hero.id} took a deep breath and came clean with a sigh,")
    world.say(f"'I made a mistake, and I wanted to hide it, oh my.'")
    world.say(f"That honest small sentence made room for repair;")
    world.say(f"{adult.label} smiled, and the stain got less scary to wear.")

    world.para()
    world.say(f"They wiped the bright blot, and they mended the page,")
    world.say(f"then wrote a new verse that would dance on the stage.")
    world.say(f"{hero.id} was not a faker by the end of the light;")
    world.say(f"{hero.id} was a kinder young writer, all warm and all right.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prob = f["problem"]
    lesson = f["lesson"]
    return [
        f'Write a rhyming story for young children about a faker, a {prob.stain_word}, and {hero.id} learning {lesson.label}.',
        f"Tell a short poem-like story where {hero.id} makes a mistake, tells the truth, and becomes kinder.",
        f'Create a gentle rhyming story that includes the words "faker", "author", and "{prob.stain_word}" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    prob = f["problem"]
    lesson = f["lesson"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little faker who wanted to make a page look perfect but had to face the {prob.stain_word}.",
        ),
        QAItem(
            question=f"What trouble did {hero.id} have?",
            answer=f"{hero.id} had a {prob.stain_word} on the page after trying to {prob.verb}.",
        ),
        QAItem(
            question=f"What lesson was learned at the end?",
            answer=f"{hero.id} learned {lesson.label}: it was better to tell the truth kindly than to hide the mistake.",
        ),
        QAItem(
            question=f"How did the transformation happen?",
            answer=f"After {adult.label} encouraged honesty, {hero.id} changed from a faker into a kinder, more truthful writer.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stain?",
            answer="A stain is a mark that makes something look dirty or changed in a way that is hard to erase.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a big change from one state or way of being into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts_only() -> str:
    return asp_facts()


def asp_program_full(show: str) -> str:
    return f"{asp_facts_only()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="nook", problem="stain", lesson="kindness", name="Mia", gender="girl", trait="gentle"),
    StoryParams(place="table", problem="ink", lesson="truth", name="Leo", gender="boy", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_full("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_full("#show story_ok/3."))
        combos = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.name}: {p.problem} / {p.lesson} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
