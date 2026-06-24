#!/usr/bin/env python3
"""
storyworlds/worlds/penis_pistachio_vex_friendship_magic_bad_ending.py
======================================================================

A small mystery-leaning story world about friendship, a little magic, and a
bad ending that follows from the world state.

Seed tale sketch:
---
Two friends, Mina and Jo, find a shiny pistachio-green charm in the hedgerow.
When they touch it, the charm makes little clues appear: a scribble on the gate,
a ringing bell, and a word no one understands: "penis." Jo laughs, Mina feels
vexed, and both try to solve the puzzle. They follow the clues through the dusk,
but the magic only makes them argue more. At last, the charm disappears into the
dark hedge, leaving the friends apart and the mystery unsolved.

World model:
---
- Friendship is a shared social meter that can help or break.
- Magic is a physical force that reveals clues, but it can also mislead.
- Vex is a frustration meter that rises when clues do not fit.

This script keeps the prose concrete and causal: the ending image depends on the
state of the friendship, the vexation, and whether the magic was handled well.
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
    kind: str = "thing"  # character | thing | place
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.id

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the hedge lane"
    mood: str = "misty"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    risk: str
    reveals: str
    weight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


SETTINGS = {
    "hedge": Setting(place="the hedge lane", mood="misty", affords={"pistachio"}),
    "garden": Setting(place="the back garden", mood="dusky", affords={"pistachio"}),
    "attic": Setting(place="the attic room", mood="dim", affords={"magic"}),
}

CLUES = {
    "pistachio": Clue(
        id="pistachio",
        text="a pistachio-green charm",
        risk="strange",
        reveals="a small clue",
        weight="light",
        tags={"pistachio", "magic", "mystery"},
    ),
    "vex": Clue(
        id="vex",
        text="a vexing little whisper",
        risk="confusing",
        reveals="more trouble",
        weight="thin",
        tags={"vex", "mystery"},
    ),
    "penis": Clue(
        id="penis",
        text="the odd word on the gate",
        risk="shocking",
        reveals="no answer at all",
        weight="sharp",
        tags={"penis", "mystery"},
    ),
}

NAMES_A = ["Mina", "Lia", "June", "Tess", "Nora", "Ivy"]
NAMES_B = ["Jo", "Ben", "Oli", "Kai", "Pip", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery-leaning story world about friendship, magic, and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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


def reasonableness_gate(place: str, clue: str) -> bool:
    return place in SETTINGS and clue in CLUES and clue in SETTINGS[place].affords or clue == "vex" or clue == "penis"


ASP_RULES = r"""
place(hedge).
place(garden).
place(attic).

clue(pistachio).
clue(vex).
clue(penis).

affords(hedge,pistachio).
affords(garden,pistachio).
affords(attic,magic).

reasonable(P,C) :- affords(P,C).
reasonable(P,vex).
reasonable(P,penis).

#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return set(asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    py = set()
    for p in SETTINGS:
        for c in CLUES:
            if reasonableness_gate(p, c):
                py.add((p, c))
    cl = asp_reasonable()
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} reasonable pairs).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue and not reasonableness_gate(args.place, args.clue):
        raise StoryError("That clue does not fit the chosen place.")
    choices = [(p, c) for p in SETTINGS for c in CLUES if reasonableness_gate(p, c)]
    if args.place:
        choices = [x for x in choices if x[0] == args.place]
    if args.clue:
        choices = [x for x in choices if x[1] == args.clue]
    if not choices:
        raise StoryError("No reasonable mystery matches the given options.")
    place, clue = rng.choice(sorted(choices))
    return StoryParams(
        place=place,
        clue=clue,
        name_a=args.name_a or rng.choice(NAMES_A),
        name_b=args.name_b or rng.choice(NAMES_B),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the words "{f["clue"].id}", "friendship", and "magic".',
        f"Tell a gentle but tense story about two friends, {f['a'].id} and {f['b'].id}, who find a clue at {f['setting'].place}.",
        f'Write a story where a small clue seems helpful at first, then turns vexing, and the ending is a bad one.',
    ]


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    a = world.add(Entity(id=params.name_a, kind="character", traits=["curious", "careful"]))
    b = world.add(Entity(id=params.name_b, kind="character", traits=["brave", "talkative"]))
    clue = CLUES[params.clue]
    prop = world.add(Entity(id=clue.id, kind="thing", label=clue.text, phrase=clue.text))
    world.facts.update(a=a, b=b, clue=clue, prop=prop, setting=world.setting)
    return world


def apply_story(world: World) -> None:
    a = world.facts["a"]
    b = world.facts["b"]
    clue = world.facts["clue"]
    prop = world.facts["prop"]

    a.memes["friendship"] = 2.0
    b.memes["friendship"] = 2.0
    a.memes["curiosity"] = 1.0
    b.memes["curiosity"] = 1.0

    world.say(f"On a misty evening, {a.id} and {b.id} walked along {world.setting.place}.")
    world.say(f"They were best friends, and they liked to solve small mysteries together.")
    world.say(f"Then they found {prop.label} tucked near the fence.")

    world.para()
    world.say(f"At first, the charm looked friendly. It gave off a soft pistachio glow.")
    world.say(f"A tiny line of magic shimmered in the air, and a clue appeared: {clue.reveals}.")
    a.meters["magic"] = 1.0
    b.meters["magic"] = 1.0

    if clue.id == "pistachio":
        a.memes["hope"] = 1.0
        b.memes["hope"] = 1.0
        a.memes["vex"] = 0.5
        b.memes["vex"] = 0.5
        world.say(f"{a.id} thought the charm might point to something important.")
        world.say(f"{b.id} thought it was fun, but the clue was too small to explain itself.")
    elif clue.id == "vex":
        a.memes["vex"] = 2.0
        b.memes["vex"] = 1.0
        world.say(f"The whisper made {a.id} vexed, because it did not answer any question.")
        world.say(f"{b.id} laughed at first, but soon even {b.pronoun('subject')} grew uneasy.")
    else:
        a.memes["vex"] = 2.0
        b.memes["vex"] = 2.0
        world.say(f"The odd word on the gate puzzled them both.")
        world.say(f"No one knew what it meant, and that made the mystery feel cold.")

    world.para()
    world.say("They followed the clue deeper into the lane.")
    world.say(f"Each new sign looked useful for a moment, and then it slipped away.")
    a.memes["friendship"] -= 1.0
    b.memes["friendship"] -= 1.0
    a.memes["vex"] = a.memes.get("vex", 0.0) + 1.0
    b.memes["vex"] = b.memes.get("vex", 0.0) + 1.0
    world.say(f"{a.id} wanted to keep guessing, but {b.id} began to argue.")
    world.say("The magic did not help them listen better. It only made the clues look prettier.")

    world.para()
    a.memes["friendship"] = max(0.0, a.memes.get("friendship", 0.0) - 1.0)
    b.memes["friendship"] = max(0.0, b.memes.get("friendship", 0.0) - 1.0)
    world.say("At last the charm slipped into the dark hedge and vanished.")
    if a.memes.get("friendship", 0.0) < THRESHOLD or b.memes.get("friendship", 0.0) < THRESHOLD:
        world.say(f"{a.id} and {b.id} stood apart in the hush, both vexed and neither one smiling.")
        world.say("They went home without solving the mystery, and the bad ending felt real and quiet.")

    world.facts["bad_ending"] = True
    world.facts["resolved"] = False


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The two friends are {a.id} and {b.id}. They go together to {world.setting.place} and try to solve the mystery.",
        ),
        QAItem(
            question=f"What magical thing did they find?",
            answer=f"They found {clue.text}. It gave them a clue, but the clue did not stay clear for long.",
        ),
        QAItem(
            question=f"Why did the ending feel bad?",
            answer="The ending felt bad because the friends became more vexed instead of working together, and the magic clue disappeared before they could solve the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm bond between people who care about each other and try to help each other.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something strange and wonderful can happen, even when nobody understands how it works.",
        ),
        QAItem(
            question="What does vexed mean?",
            answer="Vexed means annoyed, puzzled, or upset because something is not going the way you hoped.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hedge", clue="pistachio", name_a="Mina", name_b="Jo"),
    StoryParams(place="garden", clue="vex", name_a="Tess", name_b="Ben"),
    StoryParams(place="hedge", clue="penis", name_a="Lia", name_b="Kai"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    apply_story(world)
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


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def build_asp_text() -> str:
    return asp_program("#show reasonable/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} reasonable pairs:")
        for p, c in pairs:
            print(f"  {p:8} {c}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name_a} and {p.name_b}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
