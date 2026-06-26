#!/usr/bin/env python3
"""
A small ghost-story world: a timid child, a harmless haunting, a warranty
promise, and a brave choice.

The seed tale behind this world:
---
A child found a little brass lantern in the attic with a warranty card tucked
inside the box. At night the lantern whispered, and the child feared the dark
hallway. The child kept hearing the same soft sound again and again. Then the
child remembered to be humble, took a slow breath, and walked toward the
whisper. The lantern was only asking to be lit so it could consume one tiny
candle. When the child did that, the hallway glowed, the whisper stopped,
and the child felt braver than before.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    affords: set[str] = field(default_factory=lambda: {"listen", "light", "walk"})


@dataclass
class Tale:
    verb: str
    echo: str
    risk: str
    turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str


@dataclass
class StoryParams:
    place: str
    tale: str
    prize: str
    name: str
    gender: str
    age_word: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "attic": Setting(place="the old attic"),
    "hallway": Setting(place="the hallway"),
    "parlor": Setting(place="the dim parlor"),
}

TALES = {
    "whisper": Tale(
        verb="listen to the whisper",
        echo="the whisper came again, soft and patient, again and again",
        risk="the child feared the dark hallway",
        turn="the lantern only wanted to be lit",
        keyword="whisper",
        tags={"ghost", "echo"},
    ),
    "tap": Tale(
        verb="follow the tapping",
        echo="tap, tap, tap, the sound kept repeating from the wall",
        risk="the tapping made the child hold very still",
        turn="the tapping was only a branch touching the glass",
        keyword="tap",
        tags={"ghost", "echo"},
    ),
    "rustle": Tale(
        verb="follow the rustle",
        echo="the rustle repeated like a tiny skirt of leaves moving in the dark",
        risk="the child thought something unseen was near",
        turn="the rustle came from a paper fan stirring the air",
        keyword="rustle",
        tags={"ghost", "echo"},
    ),
}

PRIZES = {
    "lantern": Prize("lantern", "a little brass lantern", "lantern"),
    "candle": Prize("candle", "one tiny candle", "candle"),
    "key": Prize("key", "an old silver key", "key"),
}

NAMES = ["Mina", "Theo", "Lina", "Eli", "Nora", "Owen", "Ivy", "June"]
AGE_WORDS = ["small", "little", "young", "tiny"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for tale_id in TALES:
            for prize_id in PRIZES:
                if place in {"attic", "parlor"} and tale_id in {"whisper", "tap", "rustle"}:
                    out.append((place, tale_id, prize_id))
    return out


def reject_reason(place: str, tale: str, prize: str) -> str:
    return (
        f"(No story: {prize} does not fit the ghostly turn for {tale} in {place}. "
        f"Choose one of the supported combinations.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    tale = TALES[params.tale]
    prize = PRIZES[params.prize]

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"bravery": 0.0},
        memes={"humility": 0.0, "fear": 0.0, "hope": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        meters={"fade": 0.0},
        memes={"restlessness": 1.0},
    ))
    item = world.add(Entity(
        id=prize.type,
        kind="thing",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=child.id,
        caretaker=child.id,
        meters={"warranty": 1.0},
    ))
    world.facts.update(child=child, ghost=ghost, item=item, tale=tale, prize=prize, params=params)

    world.say(f"{params.name} was a {params.age_word} child in {setting.place} who liked quiet corners and dim light.")
    world.say(f"{params.name} kept a {prize.phrase} with a warranty tucked safely inside the box.")
    world.say(f"At night, {tale.echo}.")
    world.say(f"{params.name} wanted to {tale.verb}, but {tale.risk}.")

    world.para()
    child.memes["fear"] += 1
    world.say(f'In a small inner monologue, {params.name} thought, "I should stay still. I should stay still. I should stay still."')
    world.say(f'But another thought answered back: "Be humble. Be humble. Learn first, then move."')
    child.memes["humility"] += 1
    world.say(f"{params.name} took a slow breath and walked anyway, because bravery can be quiet.")

    world.para()
    child.meters["bravery"] += 1
    ghost.memes["restlessness"] -= 1
    world.say(f"{tale.turn}.")
    if params.prize == "candle":
        world.say(f"{params.name} lit the candle, and the lantern could finally consume its tiny flame without fear.")
        item.meters["warranty"] -= 1
    elif params.prize == "lantern":
        world.say(f"{params.name} opened the lantern and let its warm glass consume the darkness in a little circle on the floor.")
        item.meters["warranty"] -= 1
    else:
        world.say(f"{params.name} lifted the key, and the key fit a hidden drawer where the whisper had been waiting.")
        item.meters["warranty"] -= 1

    world.say(f"The sound did not sound scary anymore. It sounded lonely, then gentle, then gone.")
    world.say(f"{params.name} felt small and proud at the same time, which is a very brave kind of feeling.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    t = world.facts["tale"]
    pr = world.facts["prize"]
    return [
        f"Write a ghost story for a young child about {p.name}, a {pr.phrase}, and a repeating {t.keyword}.",
        f"Tell a short haunted-house story that includes the words warranty, consume, and humble.",
        f"Make a gentle spooky tale where a child uses inner monologue, repetition, and bravery to face a whisper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    t = world.facts["tale"]
    pr = world.facts["prize"]
    child = world.facts["child"]
    qs = [
        QAItem(
            question=f"What did {p.name} keep in the box?",
            answer=f"{p.name} kept {pr.phrase} in the box, and it had a warranty card tucked safely inside.",
        ),
        QAItem(
            question=f"Why did {p.name} feel scared before going into {world.setting.place}?",
            answer=f"{p.name} felt scared because {t.risk}, and the repeated sound made the dark feel bigger.",
        ),
        QAItem(
            question=f"What helped {p.name} keep going?",
            answer=f"An inner monologue, a humble thought, and quiet bravery helped {p.name} keep going.",
        ),
    ]
    if world.facts.get("resolved"):
        qs.append(QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The repeating sound stopped feeling frightening, and {p.name} ended up brave and calm.",
        ))
    return qs


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warranty?",
            answer="A warranty is a promise that something will work or be helped if it has a problem.",
        ),
        QAItem(
            question="What does consume mean?",
            answer="To consume means to use something up, like a candle flame consuming wax or a fire consuming wood.",
        ),
        QAItem(
            question="What does humble mean?",
            answer="Humble means not acting proud and being ready to learn or listen.",
        ),
        QAItem(
            question="What is a brave choice?",
            answer="A brave choice is doing the right thing even when you feel nervous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,R) :- place(P), tale(T), prize(R), ghosty(T), fit(P,T,R).
ghosty(whisper). ghosty(tap). ghosty(rustle).
fit(attic,_,_). fit(parlor,_,_). fit(hallway,_,_) :- false.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TALES:
        lines.append(asp.fact("tale", t))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with humble bravery and a warranty-lit lantern.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--age-word", choices=AGE_WORDS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.tale:
        combos = [c for c in combos if c[1] == args.tale]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid story combination matches the given options.)")
    place, tale, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    age = args.age_word or rng.choice(AGE_WORDS)
    return StoryParams(place=place, tale=tale, prize=prize, name=name, gender=gender, age_word=age)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


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
    StoryParams(place="attic", tale="whisper", prize="lantern", name="Mina", gender="girl", age_word="little"),
    StoryParams(place="attic", tale="tap", prize="candle", name="Theo", gender="boy", age_word="young"),
    StoryParams(place="parlor", tale="rustle", prize="key", name="Nora", gender="girl", age_word="small"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            i += 1
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
