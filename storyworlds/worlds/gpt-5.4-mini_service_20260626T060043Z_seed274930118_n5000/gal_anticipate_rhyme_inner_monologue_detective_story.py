#!/usr/bin/env python3
"""
storyworlds/worlds/gal_anticipate_rhyme_inner_monologue_detective_story.py
=========================================================================

A small detective-story world about a gal who likes to anticipate clues,
think in an inner monologue, and solve a mystery through a little rhyme.

Seed tale:
---
A clever gal detective loved to anticipate trouble before it got too big.
One afternoon, a small thing went missing in town. She walked the scene,
listened to her own thoughts, and found a tiny rhyme that pointed the way.
By following the rhyme, she discovered the hidden thing and brought the
day back to calm.
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
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "gal", "detective"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    missing_label: str
    missing_phrase: str
    suspect: str
    hiding_place: str
    rhyme: str
    solution_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    case: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "library": Setting(place="the library", mood="quiet", affords={"search"}),
    "bakery": Setting(place="the bakery", mood="warm", affords={"search"}),
    "garden": Setting(place="the garden", mood="green", affords={"search"}),
}

CASES = {
    "missing_key": Case(
        id="missing_key",
        missing_label="key",
        missing_phrase="a tiny brass key",
        suspect="the wind",
        hiding_place="under the welcome mat",
        rhyme="If you seek the shiny key, look where shoes may wait for tea.",
        solution_line="The welcome mat had a little bump, and under it was the brass key.",
        tags={"key", "rhyme"},
    ),
    "missing_cookie": Case(
        id="missing_cookie",
        missing_label="cookie",
        missing_phrase="a sugar cookie with a blue dot",
        suspect="a hungry bird",
        hiding_place="inside a teacup",
        rhyme="If you seek the spotted treat, check the cup beside your seat.",
        solution_line="Inside the teacup sat the cookie, safe and crumb-free.",
        tags={"cookie", "rhyme"},
    ),
    "missing_bookmark": Case(
        id="missing_bookmark",
        missing_label="bookmark",
        missing_phrase="a red ribbon bookmark",
        suspect="a busy kitten",
        hiding_place="behind a potted fern",
        rhyme="If you seek the ribbon bright, peek behind the leafy light.",
        solution_line="Behind the fern, the ribbon bookmark waited like a flag.",
        tags={"bookmark", "rhyme"},
    ),
}

CURATED = [
    StoryParams(setting="library", case="missing_bookmark", name="Mina"),
    StoryParams(setting="bakery", case="missing_cookie", name="Lena"),
    StoryParams(setting="garden", case="missing_key", name="Nora"),
]


@dataclass
class StoryState:
    clue_seen: bool = False
    anticipated: bool = False
    solved: bool = False


def valid_combos() -> list[tuple[str, str]]:
    return [
        ("library", "missing_bookmark"),
        ("bakery", "missing_cookie"),
        ("garden", "missing_key"),
    ]


def intro(world: World, hero: Entity, case: Case) -> None:
    hero.memes["curiosity"] = 1.0
    hero.memes["anticipation"] = 1.0
    world.say(
        f"{hero.id} was a clever gal detective who liked to anticipate trouble "
        f"before it grew big."
    )
    world.say(
        f"She kept her coat neat, her eyes sharp, and her thoughts even sharper."
    )
    world.say(
        f"That day, someone had lost {case.missing_phrase}, and the whole place felt a little off."
    )


def arrival(world: World, hero: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} arrived at {world.setting.place} and looked at every corner, "
        f"as if the room itself might whisper a clue."
    )
    world.say(
        f"In her inner monologue, she thought, 'A small mystery leaves a small trail. "
        f"I only need to notice the trail first.'"
    )


def clue_and_rhyme(world: World, hero: Entity, case: Case, state: StoryState) -> None:
    state.clue_seen = True
    hero.meters["clues"] = hero.meters.get("clues", 0.0) + 1
    hero.memes["anticipation"] = hero.memes.get("anticipation", 0.0) + 1
    world.say(
        f"Near the front of the room, {hero.id} found a note with a tiny rhyme on it: "
        f"'{case.rhyme}'"
    )
    world.say(
        f"She read it once, then twice, and her inner monologue hummed, "
        f"'That rhyme is not random. It is pointing somewhere on purpose.'"
    )
    state.anticipated = True


def search(world: World, hero: Entity, case: Case, state: StoryState) -> None:
    world.say(
        f"{hero.id} followed the rhyme step by step, moving from the bright spot "
        f"to the quiet spot without making a fuss."
    )
    world.say(
        f"She checked the place the clue suggested, because a good detective "
        f"does not rush past a careful hint."
    )
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1


def solve(world: World, hero: Entity, case: Case, state: StoryState) -> None:
    state.solved = True
    hero.meters["found"] = hero.meters.get("found", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(case.solution_line)
    world.say(
        f"{hero.id} smiled in relief and said, 'I anticipated the clue, and the clue anticipated me.'"
    )
    world.say(
        f"The missing {case.missing_label} was back where it belonged, and the whole day felt tidy again."
    )


def tell(setting: Setting, case: Case, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl", label=name))
    world.facts["hero"] = hero
    world.facts["case"] = case
    world.facts["setting"] = setting

    intro(world, hero, case)
    world.para()
    arrival(world, hero, case)
    world.para()
    state = StoryState()
    clue_and_rhyme(world, hero, case, state)
    search(world, hero, case, state)
    world.para()
    solve(world, hero, case, state)

    world.facts["state"] = state
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a short detective story for a child about a gal named {hero.id} who likes to anticipate clues.",
        f"Tell a gentle mystery set at {setting.place} where a rhyme helps find {case.missing_phrase}.",
        f"Write a story with inner monologue and a rhyme that leads a girl detective to a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    state: StoryState = world.facts["state"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{hero.id}, a clever gal detective, solved it by following a rhyme and listening to her inner monologue.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{case.missing_phrase} was missing, and the clue led {hero.id} to it.",
        ),
        QAItem(
            question="How did the detective know where to look?",
            answer=(
                f"She anticipated that the rhyme was a clue, so she searched the place it pointed to "
                f"and found the missing {case.missing_label}."
            ),
        ),
    ] + (
        [
            QAItem(
                question="What did the detective think to herself?",
                answer="Her inner monologue told her that a small mystery leaves a small trail, so she should follow the trail carefully.",
            ),
            QAItem(
                question="Did the story end happily?",
                answer="Yes. The missing thing was found, and the day became calm again.",
            ),
        ] if state.solved else []
    )


WORLD_KNOWLEDGE = {
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a word sound pattern where the endings sound alike, like cat and hat.",
        )
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        )
    ],
    "inner_monologue": [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head when you think to yourself.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ("detective", "inner_monologue", "rhyme") for q in WORLD_KNOWLEDGE[key]]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting_valid(S) :- setting(S).
case_valid(C) :- case(C).

valid_story(S, C) :- setting_valid(S), case_valid(C), compatible(S, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for s, c in valid_combos():
        lines.append(asp.fact("compatible", s, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world with rhyme and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
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
    combos = valid_combos()
    if args.place or args.case:
        combos = [
            (s, c) for s, c in combos
            if (args.place is None or s == args.place) and (args.case is None or c == args.case)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Mina", "Lena", "Nora", "Iris", "Tess"])
    return StoryParams(setting=setting, case=case, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CASES[params.case], params.name)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_stories()
        print(f"{len(combos)} compatible stories:\n")
        for setting, case in combos:
            print(f"  {setting:8} {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
