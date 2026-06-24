#!/usr/bin/env python3
"""
Storyworld: suburban whodunit with a hook, a clue trail, and a lesson learned.

A small, self-contained simulation of a child-friendly mystery in a suburban
neighborhood. The story begins with a hook-shaped clue, builds suspense around
a missing object, turns on diagnosis of the clues, and ends with a lesson about
not jumping to conclusions.

The narrative style aims at whodunit: suspicion, evidence, reveal, resolution.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the suburban street"
    houses: int = 6
    quiet: bool = True


@dataclass
class Mystery:
    missing: str
    missing_phrase: str
    culprit: str
    culprit_type: str
    clue_item: str
    clue_phrase: str
    clue_kind: str
    reveal_method: str
    lesson: str


@dataclass
class StoryParams:
    mystery: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


MYSTERIES = {
    "cookie": Mystery(
        missing="cookie",
        missing_phrase="a warm chocolate chip cookie",
        culprit="dog",
        culprit_type="dog",
        clue_item="hook",
        clue_phrase="a small metal hook on the garden gate",
        clue_kind="hook",
        reveal_method="diagnose",
        lesson="look at clues before blaming someone",
    ),
    "kite": Mystery(
        missing="kite",
        missing_phrase="a red kite with a long tail",
        culprit="squirrel",
        culprit_type="squirrel",
        clue_item="ribbon",
        clue_phrase="a ribbon snagged on the hook by the porch",
        clue_kind="ribbon",
        reveal_method="diagnose",
        lesson="slow down and follow the evidence",
    ),
    "key": Mystery(
        missing="key",
        missing_phrase="the spare house key",
        culprit="child",
        culprit_type="child",
        clue_item="hook",
        clue_phrase="the hook by the mailbox",
        clue_kind="hook",
        reveal_method="diagnose",
        lesson="ask kindly before making guesses",
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lila", "Zoe", "Ivy", "Ella"],
    "boy": ["Ben", "Leo", "Max", "Owen", "Noah", "Theo"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suburban whodunit storyworld.")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    return [(m, g) for m in sorted(MYSTERIES) for g in ("girl", "boy")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gender and args.name is None:
        pass
    combos = valid_combos()
    if args.mystery:
        combos = [c for c in combos if c[0] == args.mystery]
    if args.gender:
        combos = [c for c in combos if c[1] == args.gender]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mystery, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(mystery=mystery, name=name, gender=gender, parent=parent)


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    clue = world.add(Entity(id="clue", type="thing", label=world.mystery.clue_item, phrase=world.mystery.clue_phrase))
    missing = world.add(Entity(id="missing", type="thing", label=world.mystery.missing, phrase=world.mystery.missing_phrase, owner=hero.id))
    culprit = world.add(Entity(id="culprit", kind="character", type=world.mystery.culprit_type, label=world.mystery.culprit))
    world.facts.update(hero=hero, parent=parent, clue=clue, missing=missing, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    mystery = MYSTERIES[params.mystery]
    world = World(Setting(), mystery)
    _setup(world, params)
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    parent: Entity = world.facts["parent"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    missing: Entity = world.facts["missing"]  # type: ignore[assignment]
    culprit: Entity = world.facts["culprit"]  # type: ignore[assignment]

    hero.memes["curious"] = 1
    hero.memes["suspense"] = 1
    world.say(f"On a quiet suburban street, {hero.id} noticed something odd: {missing.phrase} was gone.")
    world.say(f"Right beside the porch, {clue.phrase} glinted like a tiny secret.")
    world.say(f"{hero.id} frowned and started to {mystery.reveal_method} the scene like a little detective.")

    world.para()
    hero.memes["suspense"] += 1
    hero.memes["conflict"] = 1
    world.say(f"At first, {hero.id} thought {parent.pronoun('object')} might know where it was.")
    world.say(f"But then a soft sound came from the hedge, and the mystery felt bigger and stranger.")
    world.say(f"{hero.id} wanted to guess fast, but {parent.pronoun('possessive')} careful eyes said to look again.")

    world.para()
    hero.memes["diagnosed"] = 1
    world.say(f"{hero.id} followed the clue to the garden gate and saw why the hook mattered.")
    if mystery.culprit_type == "dog":
        world.say("A muddy paw print and a missing biscuit wrapper matched the trail.")
    elif mystery.culprit_type == "squirrel":
        world.say("A twitchy tail left tiny crumbs and a strip of ribbon caught on a branch.")
    else:
        world.say("A jiggling key ring had slipped off the hook and landed in the flower pot.")
    world.say(f"That was when the truth clicked: {culprit.label} had done it, not {parent.pronoun('subject')}.")

    world.para()
    hero.memes["conflict"] = 0
    hero.memes["lesson"] = 1
    world.say(f"{hero.id} apologized for the wrong guess, and {parent.pronoun('subject')} gave a small smile.")
    world.say(f"They fixed the little mess together, and {hero.id} learned to {mystery.lesson}.")
    world.say(f"By bedtime, the hook was tidy, the missing thing was found, and the street felt calm again.")

    world.facts.update(params=params, resolved=True)
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery: Mystery = world.mystery
    return [
        f'Write a gentle whodunit for a young child about a suburban mystery with the word "{mystery.clue_kind}".',
        f"Tell a short story where {hero.id} has to {mystery.reveal_method} a clue and find out who took the {mystery.missing}.",
        f"Write a suspenseful but safe mystery story set on a suburban street with a hook-shaped clue and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    clue: Entity = f["clue"]  # type: ignore[assignment]
    missing: Entity = f["missing"]  # type: ignore[assignment]
    culprit: Entity = f["culprit"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery
    return [
        QAItem(
            question=f"What strange thing did {hero.id} notice missing on the suburban street?",
            answer=f"{hero.id} noticed that {missing.phrase} was gone.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} diagnose the mystery?",
            answer=f"The clue was {clue.phrase}. It helped {hero.id} follow the evidence carefully.",
        ),
        QAItem(
            question=f"Who did the story reveal as the one who caused the mystery?",
            answer=f"The story revealed {culprit.label}. That was the real answer after {hero.id} looked closely.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned to {mystery.lesson}. That was the lesson learned after the truth came out.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does suburban mean?",
            answer="Suburban means in a neighborhood with houses, yards, and streets near a town or city.",
        ),
        QAItem(
            question="What is a hook?",
            answer="A hook is a bent piece of metal used to hang or hold something in place.",
        ),
        QAItem(
            question="What does diagnose mean?",
            answer="Diagnose means to look at clues and figure out what is really going on.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(M) :- chosen(M,_).
suburban_scene :- mystery(_).
has_hook(M) :- chosen(M,_), hook_clue(M).
suspense(M) :- suburban_scene, has_hook(M).
conflict(M) :- suspense(M), wrong_guess(M).
lesson_learned(M) :- conflict(M), reveal(M).
valid_story(M) :- lesson_learned(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for m, mystery in MYSTERIES.items():
        lines.append(asp.fact("chosen", m, mystery.culprit_type))
        lines.append(asp.fact("hook_clue", m) if mystery.clue_kind == "hook" else asp.fact("clue_kind", m, mystery.clue_kind))
        lines.append(asp.fact("wrong_guess", m))
        lines.append(asp.fact("reveal", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("cookie",), ("kite",), ("key",)}
    if clingo_set == python_set:
        print("OK: clingo gate matches valid_story set.")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


CURATED = [
    StoryParams(mystery="cookie", name="Mia", gender="girl", parent="mother"),
    StoryParams(mystery="kite", name="Ben", gender="boy", parent="father"),
    StoryParams(mystery="key", name="Nora", gender="girl", parent="mother"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
