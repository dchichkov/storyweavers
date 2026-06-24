#!/usr/bin/env python3
"""
storyworlds/worlds/philosophy_transformation_lesson_learned_mystery_to_solve.py
================================================================================

A small comedy-leaning storyworld about philosophy, a transformation, a lesson
learned, and a mystery to solve.

Seed tale used to build the world model:
---
A curious kid named Nia found a strange shiny pebble in the schoolyard. Every
time she asked a big question about life, the pebble changed into a different
shape: first a spoon, then a tiny key, then a paper star.

Nia could not figure out why it was changing. She asked her teacher, who said
that some mysteries only make sense when you look at them from another angle.
Nia started testing her guesses. She learned that asking questions was not the
same as complaining, and that thinking could be funny too.

At last, she noticed the pebble changed only when someone answered a question
with care. Nia smiled, shared the finding with her class, and the pebble became
a little mirror. Everyone laughed, because the biggest mystery had been hiding
a very small lesson all along.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    plural: bool = False
    forms: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the schoolyard"
    indoors: bool = False
    quiet: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    question: str
    clue: str
    reveal: str
    trigger: str


@dataclass
class Transformation:
    id: str
    forms: list[str]
    cue: str
    final_form: str
    lesson: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


GIRL_NAMES = ["Nia", "Maya", "Luna", "Ivy", "Zoe", "Mina", "Tess", "Ada"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Leo", "Max", "Toby", "Ben", "Theo"]
TEACHER_NAMES = ["Ms. Bean", "Mr. Quill", "Ms. Dot", "Mr. Lark"]
TRAITS = ["curious", "serious", "playful", "careful", "thoughtful", "silly"]


SETTINGS = {
    "schoolyard": Setting(place="the schoolyard", indoors=False, quiet=False, affords={"question"}),
    "library": Setting(place="the library", indoors=True, quiet=True, affords={"question"}),
    "classroom": Setting(place="the classroom", indoors=True, quiet=False, affords={"question"}),
}

MYSTERIES = {
    "pebble": Mystery(
        id="pebble",
        label="pebble",
        phrase="a shiny pebble",
        question="Why does the pebble keep changing shape?",
        clue="the pebble changes when someone answers a question with care",
        reveal="it was a kindness mirror in disguise",
        trigger="care",
    ),
    "box": Mystery(
        id="box",
        label="box",
        phrase="a little cardboard box",
        question="Why does the box make a tiny giggle sound?",
        clue="the box giggles when someone asks a very honest question",
        reveal="it was listening for honest questions",
        trigger="honest",
    ),
    "button": Mystery(
        id="button",
        label="button",
        phrase="a bright button",
        question="Why does the button keep turning into new shapes?",
        clue="the button changes when someone thinks before speaking",
        reveal="it was teaching patience",
        trigger="patient",
    ),
}

TRANSFORMATIONS = {
    "pebble": Transformation(
        id="pebble",
        forms=["spoon", "tiny key", "paper star", "mirror"],
        cue="care",
        final_form="mirror",
        lesson="kind answers can change a problem into a clue",
    ),
    "box": Transformation(
        id="box",
        forms=["cup", "hat", "smiling envelope", "lantern"],
        cue="honest",
        final_form="lantern",
        lesson="truthful questions can light up a mystery",
    ),
    "button": Transformation(
        id="button",
        forms=["coin", "leaf", "clock", "compass"],
        cue="patient",
        final_form="compass",
        lesson="patience helps you face a puzzle from the right angle",
    ),
}


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    teacher: str
    trait: str
    seed: Optional[int] = None


class MysteryWorld:
    def __init__(self, world: World, hero: Entity, teacher: Entity, mystery: Entity,
                 mystery_cfg: Mystery, trans_cfg: Transformation) -> None:
        self.world = world
        self.hero = hero
        self.teacher = teacher
        self.mystery = mystery
        self.mystery_cfg = mystery_cfg
        self.trans_cfg = trans_cfg
        self.index = 0

    def transform_once(self) -> None:
        if self.index >= len(self.trans_cfg.forms):
            return
        form = self.trans_cfg.forms[self.index]
        sig = ("transform", self.index)
        if sig in self.world.fired:
            return
        self.world.fired.add(sig)
        self.mystery.forms.append(form)
        self.index += 1
        self.mystery.meters["changed"] = self.mystery.meters.get("changed", 0) + 1

    def solve(self) -> None:
        self.mystery.memes["understood"] = 1
        self.hero.memes["wonder"] = self.hero.memes.get("wonder", 0) + 1
        self.hero.memes["joy"] = self.hero.memes.get("joy", 0) + 1
        self.teacher.memes["pride"] = self.teacher.memes.get("pride", 0) + 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comic little story world about philosophy, a mystery, and a lesson learned."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--teacher", choices=TEACHER_NAMES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place in SETTINGS for mid in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    teacher = args.teacher or rng.choice(TEACHER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, teacher=teacher, trait=trait)


def tell(setting: Setting, mystery_cfg: Mystery, trans_cfg: Transformation,
         hero_name: str, gender: str, teacher_name: str, trait: str) -> MysteryWorld:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={}))
    teacher = world.add(Entity(id="teacher", kind="character", type="teacher", label=teacher_name, meters={}, memes={}))
    mystery = world.add(Entity(id=mystery_cfg.id, type="thing", label=mystery_cfg.label, phrase=mystery_cfg.phrase,
                               forms=[mystery_cfg.phrase], meters={}, memes={}))

    mw = MysteryWorld(world, hero, teacher, mystery, mystery_cfg, trans_cfg)

    world.say(f"{hero_name} was a {trait} {gender} who loved philosophy, because big questions felt like treasure maps.")
    world.say(f"One day at {setting.place}, {hero_name} found {mystery_cfg.phrase}.")
    world.say(f"{hero_name} asked, “{mystery_cfg.question}”")

    world.para()
    world.say(f"Each time {hero_name} tried a new idea, the little object changed again.")
    mw.transform_once()
    world.say(f"First it turned into a spoon, which was a very rude answer for a mystery.")
    mw.transform_once()
    world.say(f"Then it became a tiny key, as if it wanted to unlock the next guess.")
    world.say(f"{hero_name} guessed it might be magic, a trick, or a very fancy pebble with opinions.")
    world.say(f"{teacher_name} chuckled and said, “A mystery gets smaller when you look at it from another angle.”")

    world.para()
    world.say(f"{hero_name} stopped blustering and started testing ideas carefully.")
    world.say(f"{hero_name} asked kinder questions, because philosophy is not just wondering out loud; it is listening too.")
    if mystery_cfg.trigger == "care":
        world.say(f"When {hero_name} answered the question with care, the object changed one last time.")
    elif mystery_cfg.trigger == "honest":
        world.say(f"When {hero_name} asked an honest question, the object changed one last time.")
    else:
        world.say(f"When {hero_name} paused and waited patiently, the object changed one last time.")
    mw.transform_once()
    mw.solve()

    world.say(f"It became a mirror, and everyone laughed because the big mystery had been hiding a small lesson all along.")
    world.say(f"{mystery_cfg.reveal.capitalize()}.")
    world.say(f"{hero_name} learned that a good question can be funny, careful, and useful at the same time.")
    world.facts.update(hero=hero, teacher=teacher, mystery=mystery, mystery_cfg=mystery_cfg,
                       trans_cfg=trans_cfg, setting=setting)
    return mw


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mystery_cfg = f["hero"], f["mystery_cfg"]
    return [
        f'Write a short comedy story for a child about philosophy, {mystery_cfg.label}, and a lesson learned.',
        f"Tell a gentle story where {hero.id} solves a small mystery by asking thoughtful questions.",
        f"Write a funny, child-facing story in which a mysterious object transforms several times before revealing its lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, teacher, mystery_cfg = f["hero"], f["teacher"], f["mystery_cfg"]
    trans_cfg = f["trans_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found {mystery_cfg.phrase}, which kept changing shape in a silly way.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think about the mystery?",
            answer=f"{teacher.label or teacher.id} helped by reminding {hero.id} that looking from another angle can make a mystery easier to understand.",
        ),
        QAItem(
            question=f"What did the object become at the end?",
            answer=f"It became a {trans_cfg.final_form}, which showed that the mystery was really teaching a lesson.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that careful, kind thinking can solve a puzzle and can even make the answer funny.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is philosophy?",
            answer="Philosophy is thinking carefully about big questions, like what is true, what matters, and why people think the way they do.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand right away, so you look for clues.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different form.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something useful or important that you understand after an experience.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.forms:
            bits.append(f"forms={e.forms}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    mystery_cfg = MYSTERIES[params.mystery]
    trans_cfg = TRANSFORMATIONS[params.mystery]
    mw = tell(SETTINGS[params.place], mystery_cfg, trans_cfg, params.name, params.gender, params.teacher, params.trait)
    return StorySample(
        params=params,
        story=mw.world.render(),
        prompts=generation_prompts(mw.world),
        story_qa=story_qa(mw.world),
        world_qa=world_knowledge_qa(mw.world),
        world=mw.world,
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


ASP_RULES = r"""
place(P) :- setting(P).
valid(Place, Mystery) :- place(Place), mystery(Mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="schoolyard", mystery="pebble", name="Nia", gender="girl", teacher="Ms. Bean", trait="curious"),
    StoryParams(place="library", mystery="box", name="Finn", gender="boy", teacher="Mr. Quill", trait="thoughtful"),
    StoryParams(place="classroom", mystery="button", name="Maya", gender="girl", teacher="Ms. Dot", trait="playful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic philosophy storyworld with a mysterious transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--teacher", choices=TEACHER_NAMES)
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
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        name=args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        teacher=args.teacher or rng.choice(TEACHER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
