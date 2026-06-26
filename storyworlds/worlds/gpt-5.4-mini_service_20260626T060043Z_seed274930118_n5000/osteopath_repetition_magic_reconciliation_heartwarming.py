#!/usr/bin/env python3
"""
A heartwarming storyworld about an osteopath, a little problem that keeps
coming back, a touch of gentle magic, and a warm reconciliation at the end.
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
    type: str = "person"
    label: str = ""
    role: str = ""
    age_word: str = "little"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Setting:
    place: str = "the cozy clinic"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mila"
    companion: str = "her brother"
    ache: str = "a stiff back"
    magic_item: str = "the singing lamp"
    repetition_count: int = 3


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Character] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Character) -> Character:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _words_for_count(n: int) -> str:
    return {1: "once", 2: "twice", 3: "three times", 4: "four times"}.get(n, f"{n} times")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming osteopath storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--ache")
    ap.add_argument("--magic-item")
    ap.add_argument("--repetition-count", type=int)
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


def _valid_repetition_count(n: int) -> bool:
    return 2 <= n <= 5


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    count = args.repetition_count if args.repetition_count is not None else rng.choice([2, 3, 4])
    if not _valid_repetition_count(count):
        raise StoryError("repetition count must be between 2 and 5 for a gentle, readable story.")
    name = args.name or rng.choice(["Mila", "Noah", "Tia", "Eli", "Sage", "Rosa"])
    companion = args.companion or rng.choice(["her brother", "his sister", "their mom", "their dad"])
    ache = args.ache or rng.choice(["a stiff back", "a sore neck", "a tight shoulder", "an achey hip"])
    magic_item = args.magic_item or rng.choice(["the singing lamp", "the glowing pebble", "the warm towel", "the humming bell"])
    return StoryParams(
        seed=args.seed,
        name=name,
        companion=companion,
        ache=ache,
        magic_item=magic_item,
        repetition_count=count,
    )


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Character(id=params.name, role="child", label=params.name, age_word="little"))
    osteo = world.add(Character(id="DrOak", role="osteopath", label="Dr. Oak", age_word="kind"))
    companion = world.add(Character(id="Companion", role="companion", label=params.companion, age_word="careful"))

    child.meters["ache"] = 1.0
    child.memes["worry"] = 1.0
    companion.memes["doubt"] = 1.0
    world.facts.update(child=child, osteo=osteo, companion=companion, params=params)

    world.say(
        f"{params.name} came to {world.setting.place} with {params.ache}, and {params.companion} looked worried."
    )
    world.say(
        f"Dr. Oak, the osteopath, smiled kindly and said that sometimes a body feels better after gentle care and patient hands."
    )

    world.para()
    for i in range(params.repetition_count):
        step = i + 1
        child.meters["ache"] = max(0.0, child.meters["ache"] - 0.3)
        child.memes["hope"] = child.memes.get("hope", 0.0) + 0.4
        world.say(
            f"First, Dr. Oak helped {params.name} breathe slowly {_words_for_count(step)}."
            if step == 1
            else f"Then Dr. Oak tried the same soft stretch {_words_for_count(step)}."
        )
        world.say(
            f"The {params.magic_item} gave off a gentle glow, as if it knew exactly where the sore place was."
        )
        if step < params.repetition_count:
            world.say(
                f"The ache came back a little, so Dr. Oak repeated the calm movement and reminded everyone that healing can take time."
            )

    world.para()
    child.meters["ache"] = 0.0
    child.memes["joy"] = 1.0
    companion.memes["doubt"] = 0.0
    companion.memes["relief"] = 1.0
    world.say(
        f"At last, {params.name} sat up straighter and giggled because the tight feeling was gone."
    )
    world.say(
        f"{params.companion.capitalize()} apologized for worrying so much, and Dr. Oak nodded with a warm smile. "
        f"They all agreed that kindness, patience, and a little magic can help a body mend."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about an osteopath helping {p.name} with {p.ache} using gentle repetition and a little magic.",
        f"Tell a child-friendly story where healing takes {p.repetition_count} calm tries before everyone feels better.",
        f"Write a cozy clinic story with an osteopath, a worried companion, and a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who came to the clinic with {p.ache}?",
            answer=f"{p.name} came with {p.ache}.",
        ),
        QAItem(
            question="Who helped the child feel better?",
            answer="Dr. Oak, the osteopath, helped with gentle care, calm hands, and patient stretches.",
        ),
        QAItem(
            question="What helped the healing feel a little magical?",
            answer=f"The {p.magic_item} glowed gently and made the careful treatment feel magical and comforting.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"{p.name}'s ache went away, {p.companion} felt relieved, and everyone made up with warm smiles.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an osteopath?",
            answer="An osteopath is a health professional who uses gentle hands, careful movement, and thoughtful care to help a body feel better.",
        ),
        QAItem(
            question="Why can repeating a gentle movement help?",
            answer="Repeating a gentle movement can help the body remember the safe way to move and slowly relax the tight place.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who felt upset or worried forgive each other and feel close again.",
        ),
        QAItem(
            question="Why do people use magic in a story?",
            answer="Magic in a story can make a moment feel wonder-filled and help readers imagine comfort, hope, or change.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.role:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
story(1).
osteopath(X) :- person(X), role(X,osteopath).
repetition_ok(N) :- N >= 2, N =< 5.
magic_present :- magic(_).
reconciliation :- apologized(A), forgiven(B), A != B.
#show osteopath/1.
#show repetition_ok/1.
#show magic_present/0.
#show reconciliation/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("person", "DrOak"),
            asp.fact("role", "DrOak", "osteopath"),
            asp.fact("magic", "item"),
            asp.fact("apologized", "Companion"),
            asp.fact("forgiven", "Child"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show osteopath/1. #show repetition_ok/1. #show magic_present/0. #show reconciliation/0."))
    atoms = {str(a) for a in model}
    needed = {"osteopath(DrOak)", "magic_present", "reconciliation"}
    if "repetition_ok(3)" not in atoms:
        print("MISMATCH: ASP repetition check failed.")
        return 1
    if not needed.issubset(atoms):
        print("MISMATCH: ASP facts missing.")
        return 1
    print("OK: ASP twin looks reasonable.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(name="Mila", companion="her brother", ache="a stiff back", magic_item="the singing lamp", repetition_count=3),
    StoryParams(name="Noah", companion="his sister", ache="a sore neck", magic_item="the glowing pebble", repetition_count=2),
    StoryParams(name="Tia", companion="their mom", ache="a tight shoulder", magic_item="the warm towel", repetition_count=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show repetition_ok/1."))
        return
    if args.asp:
        print(asp_program("#show osteopath/1. #show repetition_ok/1. #show magic_present/0. #show reconciliation/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
