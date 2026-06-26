#!/usr/bin/env python3
"""
A standalone storyworld for a tiny comedy about a child, a tricky phoneme,
an inner monologue, a conflict, and a transformation.

Seed premise:
A child must say a slippery phoneme for a class show, but every attempt turns
into a squeaky little disaster. The child thinks through the trouble, gets
help, changes the way they breathe and shape their mouth, and ends by making
everyone laugh in the good way.
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
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"nervous": 0.0, "skill": 0.0, "joy": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "resolve": 0.0, "comic_relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Teacher:
    id: str
    kind: str = "character"
    type: str = "teacher"
    label: str = "teacher"
    meters: dict[str, float] = field(default_factory=lambda: {"patience": 0.0, "skill": 0.0, "joy": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"calm": 0.0, "encouragement": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]


@dataclass
class PhonemeTarget:
    symbol: str
    spoken_hint: str
    mouth_shape: str
    example_word: str
    funny_mistake: str
    transformation: str
    difficulty: int = 1


@dataclass
class StoryParams:
    hero_name: str
    teacher_name: str
    phoneme: str
    seed: Optional[int] = None


class World:
    def __init__(self, target: PhonemeTarget) -> None:
        self.target = target
        self.hero: Optional[Character] = None
        self.teacher: Optional[Teacher] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.inner_monologue: list[str] = []
        self.fired: set[str] = set()

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        h = self.hero
        t = self.teacher
        lines = ["--- world model state ---"]
        if h:
            lines.append(f"hero meters={ {k: round(v, 2) for k, v in h.meters.items()} } memes={ {k: round(v, 2) for k, v in h.memes.items()} }")
        if t:
            lines.append(f"teacher meters={ {k: round(v, 2) for k, v in t.meters.items()} } memes={ {k: round(v, 2) for k, v in t.memes.items()} }")
        lines.append(f"target phoneme={self.target.symbol} example={self.target.example_word}")
        return "\n".join(lines)


PHONEMES = {
    "ph": PhonemeTarget(
        symbol="ph",
        spoken_hint="a breathy sound like the start of 'phone'",
        mouth_shape="a soft puff of air between the lips and teeth",
        example_word="phone",
        funny_mistake="pigeon",
        transformation="slower breath and a gentler lip bite",
        difficulty=2,
    ),
    "sh": PhonemeTarget(
        symbol="sh",
        spoken_hint="a hushy sound like asking for quiet",
        mouth_shape="rounded lips and a quiet stream of air",
        example_word="shell",
        funny_mistake="sail",
        transformation="round the lips like a tiny fish mouth",
        difficulty=1,
    ),
    "th": PhonemeTarget(
        symbol="th",
        spoken_hint="a tongue-out sound like in 'thumb'",
        mouth_shape="the tongue peeking between the teeth",
        example_word="thumb",
        funny_mistake="sum",
        transformation="put the tongue between the teeth and giggle through it",
        difficulty=3,
    ),
}

HERO_NAMES = ["Milo", "Zoe", "Pip", "Nora", "Bea", "Toby"]
TEACHER_NAMES = ["Ms. Juniper", "Mr. Bean", "Mrs. Light", "Coach Pea"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about phonemes, inner monologue, conflict, and transformation.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--teacher-name", choices=TEACHER_NAMES)
    ap.add_argument("--phoneme", choices=sorted(PHONEMES))
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
    phoneme = args.phoneme or rng.choice(list(PHONEMES))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    teacher_name = args.teacher_name or rng.choice(TEACHER_NAMES)
    return StoryParams(hero_name=hero_name, teacher_name=teacher_name, phoneme=phoneme)


def reasonableness_gate(params: StoryParams) -> None:
    if params.phoneme not in PHONEMES:
        raise StoryError("Unknown phoneme choice.")
    if params.hero_name == params.teacher_name:
        raise StoryError("The child and teacher need different names for the scene to make sense.")


def tell_story(params: StoryParams) -> World:
    target = PHONEMES[params.phoneme]
    world = World(target)
    hero = Character(id=params.hero_name, type="child", label="child")
    teacher = Teacher(id=params.teacher_name, label="teacher")
    world.hero = hero
    world.teacher = teacher

    world.say(
        f"{hero.id} had one big job for the class show: say the phoneme {target.symbol} without wobbling."
    )
    world.say(
        f"It looked easy on paper, but {target.symbol} was a slippery little sound, and {hero.id}'s mouth kept trying to turn it into a joke."
    )

    world.para()
    hero.memes["worry"] += 1
    hero.meters["nervous"] += 1
    world.inner_monologue.append(
        f"{hero.id} thought, 'Just one sound. Why does my mouth act like a rubber duck on a trampoline?'"
    )
    world.say(
        f"{hero.id} took a breath and tried the sound anyway, but out came a goofy {target.funny_mistake} version instead."
    )
    hero.meters["skill"] += 0.2
    hero.memes["comic_relief"] += 1

    world.say(
        f"That made the class snort, and even {teacher.id} had to cover a smile with {teacher.pronoun('possessive')} hand."
    )
    hero.memes["worry"] += 1
    teacher.memes["encouragement"] += 1

    world.para()
    world.say(
        f"{teacher.id} did not laugh at {hero.id}; {teacher.id} showed {hero.id} how to make {target.mouth_shape}."
    )
    world.say(
        f"'Try {target.transformation},' {teacher.id} said, 'and think of the word {target.example_word}.'"
    )
    hero.meters["skill"] += 0.7
    hero.meters["nervous"] = max(0.0, hero.meters["nervous"] - 0.4)
    hero.memes["resolve"] += 1

    world.say(
        f"{hero.id} tried again, this time with the {target.spoken_hint}, and the sound came out clear and bright."
    )
    hero.meters["skill"] += 0.6
    hero.meters["joy"] += 1
    teacher.meters["joy"] += 1

    world.para()
    world.say(
        f"The funny part was that the class had been expecting a squeak, but {hero.id} had learned the trick and turned the mistake into a victory lap."
    )
    world.say(
        f"{hero.id} grinned, said {target.symbol} one more time, and the whole room laughed in the happy way, because now the joke had become the solution."
    )
    hero.memes["comic_relief"] += 1
    hero.memes["worry"] = 0.0

    world.facts.update(
        hero=hero,
        teacher=teacher,
        target=target,
        transformed=True,
        conflict=True,
        inner_monologue=world.inner_monologue,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    t = world.facts["target"]
    h = world.facts["hero"]
    return [
        f"Write a funny child-friendly story about a child who must say the phoneme {t.symbol}.",
        f"Tell a comedy story where {h.id} has an inner monologue about a tricky sound and learns to say {t.example_word}.",
        f"Create a short story with a small conflict, a helpful teacher, and a transformation in the way a child speaks the sound {t.symbol}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    t = world.facts["target"]
    teacher = world.facts["teacher"]
    return [
        QAItem(
            question=f"What sound was {h.id} trying to say at the class show?",
            answer=f"{h.id} was trying to say the phoneme {t.symbol}, the little sound used in words like {t.example_word}.",
        ),
        QAItem(
            question=f"What was {h.id}'s funny problem before the help from {teacher.id}?",
            answer=f"{h.id} kept slipping into a silly mistake sound instead of saying {t.symbol} clearly, which made the room giggle.",
        ),
        QAItem(
            question=f"How did {h.id} change by the end of the story?",
            answer=f"{h.id} transformed from nervous and stuck to confident and clear, and {h.id} could say {t.symbol} the right way.",
        ),
        QAItem(
            question="What did the inner monologue sound like?",
            answer=f"{world.inner_monologue[0]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    t = world.facts["target"]
    return [
        QAItem(
            question="What is a phoneme?",
            answer="A phoneme is one small sound in a spoken language. Changing one phoneme can change a word.",
        ),
        QAItem(
            question="What does it mean to think with an inner monologue?",
            answer="An inner monologue is the private voice in your head where you think through a problem, worry, or plan.",
        ),
        QAItem(
            question="Why can a small mouth-shape change the way a sound comes out?",
            answer=f"Sounds depend on how your lips, tongue, and breath work together, so {t.spoken_hint} needs the right mouth shape.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("phoneme", k, v.symbol) for k, v in PHONEMES.items()]
    for k, v in PHONEMES.items():
        lines.append(asp.fact("has_example", k, v.example_word))
        lines.append(asp.fact("has_hint", k, v.spoken_hint))
    return "\n".join(lines)


ASP_RULES = r"""
valid_phoneme(P) :- phoneme(P,_).
showable(P) :- valid_phoneme(P), has_example(P,_), has_hint(P,_).
#show valid_phoneme/1.
#show showable/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_phoneme/1."))
    clingo_set = set(asp.atoms(model, "valid_phoneme"))
    python_set = {(k,) for k in PHONEMES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches phoneme registry ({len(clingo_set)} items).")
        return 0
    print("MISMATCH between clingo and python registry:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== (3) World knowledge ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(hero_name="Milo", teacher_name="Ms. Juniper", phoneme="ph"),
    StoryParams(hero_name="Zoe", teacher_name="Mr. Bean", phoneme="sh"),
    StoryParams(hero_name="Pip", teacher_name="Mrs. Light", phoneme="th"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show showable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show showable/1."))
        items = sorted(set(asp.atoms(model, "showable")))
        print(f"{len(items)} phoneme entries:\n")
        for (p,) in items:
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
