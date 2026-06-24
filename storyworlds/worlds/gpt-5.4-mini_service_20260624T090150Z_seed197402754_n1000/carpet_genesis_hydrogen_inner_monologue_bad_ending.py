#!/usr/bin/env python3
"""
A small detective-story world with inner monologue and a bad ending.

The premise is a child-friendly mystery: a curious detective follows clues in a
quiet house, notices a carpet stain, thinks through the case in an inner
monologue, and learns something fragile about a jar of hydrogen water and a
model called Genesis. The story can end badly when the wrong choice is made.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    region: str
    risky: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.monologue: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def mono(self, text: str) -> None:
        if text:
            self.monologue.append(text)
            self.say(f"({text})")

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.worn_by:
                bits.append(f"worn_by={e.worn_by}")
            lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
        lines.append(f"  fired rules: {sorted({a for a, *_ in self.fired})}")
        return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    sidekick: str
    setting: str
    clue: str
    seed: Optional[int] = None


SETTINGS = {
    "house": Setting(place="the old house", indoors=True, affords={"search"}),
    "study": Setting(place="the dusty study", indoors=True, affords={"search"}),
    "hall": Setting(place="the quiet hall", indoors=True, affords={"search"}),
}

CLUES = {
    "carpet": Clue(
        id="carpet",
        label="carpet",
        phrase="a thick red carpet",
        region="floor",
        risky={"spill"},
        tags={"carpet", "stain"},
    ),
    "genesis": Clue(
        id="genesis",
        label="Genesis",
        phrase="a booklet labeled Genesis",
        region="desk",
        risky={"tear"},
        tags={"genesis", "book"},
    ),
    "hydrogen": Clue(
        id="hydrogen",
        label="hydrogen jar",
        phrase="a small jar marked hydrogen",
        region="desk",
        risky={"drop"},
        tags={"hydrogen", "science"},
    ),
}

DEVICES = {
    "lamp": Device(
        id="lamp",
        label="the desk lamp",
        guards={"dark"},
        prep="turn on the desk lamp",
        tail="left the lamp on to keep looking",
    ),
    "gloves": Device(
        id="gloves",
        label="soft gloves",
        guards={"tear", "drop"},
        prep="put on soft gloves",
        tail="kept the soft gloves on for the rest of the search",
    ),
}

NAMES = ["Mina", "Leo", "Ivy", "Noah", "June", "Eli"]
SIDEKICKS = ["cat", "dog", "bird", "mouse"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world with inner monologue and a bad ending.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
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


def reasonableness_gate(clue: Clue) -> bool:
    return clue.id in {"carpet", "genesis", "hydrogen"}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    if not reasonableness_gate(CLUES[clue]):
        raise StoryError("This mystery needs one of the seeded clues: carpet, genesis, or hydrogen.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
        setting=setting,
        clue=clue,
    )


def _search(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0) + 1
    world.say(f"{detective.id} and the {world.facts['sidekick']} tiptoed into {world.setting.place}.")
    world.say(f"The case felt serious, like a tiny thundercloud wearing a hat.")
    if clue.id == "carpet":
        world.say("A stain darkened the carpet near the center of the room.")
    elif clue.id == "genesis":
        world.say("A book called Genesis sat on the desk, its cover curled at the corner.")
    else:
        world.say("A glass jar marked hydrogen waited beside a stack of notes.")
    world.mono("If I want the answer, I have to look carefully and not guess too fast.")


def _bad_choice(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    if clue.id == "carpet":
        world.say(f"{detective.id} hurried forward and spilled ink onto the carpet.")
        world.say("The stain spread like a dark little cloud, and the real clue disappeared.")
    elif clue.id == "genesis":
        world.say(f"{detective.id} pulled the Genesis booklet too hard, and a page tore.")
        world.say("That made the best clue useless, because the torn page could not be read anymore.")
    else:
        world.say(f"{detective.id} bumped the hydrogen jar, and it fell with a sad clink.")
        world.say("The jar cracked, and the note beside it got wet and blurry.")
    world.mono("Oh no. That was the wrong move, and now the mystery is slipping away.")


def _ending(world: World, detective: Entity, clue: Clue) -> None:
    world.para()
    if clue.id == "carpet":
        world.say("By the time the detective looked back, the stain on the carpet had spread.")
        world.say("The room went quiet, and the case ended badly before the answer could be found.")
    elif clue.id == "genesis":
        world.say("The torn Genesis page fluttered to the floor like a little broken wing.")
        world.say("The detective stared at the mess and knew the clue was gone for good.")
    else:
        world.say("The broken hydrogen jar left the desk cold and wet.")
        world.say("The detective had come so close, but the trail ended in a bad ending.")
    world.mono("I solved nothing today, only made the room sadder.")


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    detective = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Leo", "Noah", "Eli"} else "girl"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick))
    clue = CLUES[params.clue]
    detective.meters["courage"] = 1
    world.facts.update(detective=detective, sidekick=params.sidekick, clue=clue, setting=world.setting)

    world.say(f"{detective.id} was a small detective with sharp eyes and a careful heart.")
    world.say(f"{detective.id} liked mysteries, especially when {detective.pronoun('possessive')} {params.sidekick} stayed close.")
    world.say(f"One evening, they went to {world.setting.place}, where something important had gone wrong.")
    world.para()
    _search(world, detective, clue)
    _bad_choice(world, detective, clue)
    _ending(world, detective, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue"].label
    return [
        f'Write a short detective story for a young child that includes the word "{clue}" and an inner monologue.',
        f"Tell a mystery about {f['detective'].id} and a {f['sidekick']} in {world.setting.place} that ends badly.",
        f"Write a simple detective tale where the clue is {clue}, the detective thinks to themself, and the case goes wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    clue: Clue = f["clue"]
    sidekick = f["sidekick"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {detective.id}, who went to {place} with a {sidekick}.",
        ),
        QAItem(
            question=f"What clue did {detective.id} notice at {place}?",
            answer=f"{detective.id} noticed {clue.phrase}.",
        ),
        QAItem(
            question="How did the detective think during the case?",
            answer="The detective spoke in inner monologue, quietly thinking through the mystery while searching the room.",
        ),
        QAItem(
            question="Did the story end happily?",
            answer="No. It ended badly, because the wrong choice ruined the clue and the mystery was not solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carpet?",
            answer="A carpet is a soft floor covering you can walk on inside a house.",
        ),
        QAItem(
            question="What does genesis mean?",
            answer="Genesis means the beginning or first part of something.",
        ),
        QAItem(
            question="What is hydrogen?",
            answer="Hydrogen is a very light gas. It is a real science word.",
        ),
    ]


ASP_RULES = r"""
clue(carpet). clue(genesis). clue(hydrogen).
allowed(carpet). allowed(genesis). allowed(hydrogen).
valid(C) :- clue(C), allowed(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(asp.fact("clue", c) for c in CLUES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(c,) for c in CLUES}
    if asp_set == py_set:
        print(f"OK: clingo gate matches {len(py_set)} clues.")
        return 0
    print("Mismatch between ASP and Python:")
    print("clingo only:", sorted(asp_set - py_set))
    print("python only:", sorted(py_set - asp_set))
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
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
    StoryParams(name="Mina", sidekick="cat", setting="house", clue="carpet"),
    StoryParams(name="Leo", sidekick="dog", setting="study", clue="genesis"),
    StoryParams(name="Ivy", sidekick="mouse", setting="hall", clue="hydrogen"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(sorted(asp.atoms(model, "valid")))
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
            header = f"### {p.name}: {p.clue} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
