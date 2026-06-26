#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/entry_nudist_baba_misunderstanding_problem_solving_detective.py
==============================================================================================================================

A small detective-style story world about an entry, a nudist, and baba:
a child detective spots an odd scene, mistakes the clues, and then solves
the misunderstanding by asking good questions and following evidence.

The story premise:
- At an entry, the detective sees a nudist and baba.
- The detective thinks something bad or silly is happening.
- The clues point to a simple misunderstanding.
- Problem solving and a calm explanation set things right.

The world is intentionally compact and child-facing, but still state-driven:
physical meters track things like suspicion, confusion, and relief; memes track
feelings like worry, certainty, and trust. The prose is assembled from the live
world state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad", "baba", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    afford_entry: bool = True
    detail: str = ""


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    baba_name: str
    nudist_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _rule_confusion(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    nudist = world.entities.get("nudist")
    if not detective or not nudist:
        return out
    if detective.memes.get("suspicion", 0) >= THRESHOLD and nudist.meters.get("calm", 0) >= THRESHOLD:
        sig = ("confusion",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        _add_meter(detective, "confusion", 1)
        _add_meme(detective, "worry", 1)
        out.append("The clues did not fit together yet.")
    return out


def _rule_relief(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    baba = world.entities.get("baba")
    nudist = world.entities.get("nudist")
    if not detective or not baba or not nudist:
        return out
    if detective.memes.get("trust", 0) >= THRESHOLD and nudist.meters.get("explained", 0) >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        _add_meter(detective, "relief", 1)
        _add_meme(detective, "calm", 1)
        out.append("The mystery started to make sense.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_confusion, _rule_relief):
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)

    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
    ))
    baba = world.add(Entity(
        id="baba",
        kind="character",
        type="baba",
        label=params.baba_name,
    ))
    nudist = world.add(Entity(
        id="nudist",
        kind="character",
        type="person",
        label=params.nudist_name,
        role="nudist",
    ))

    # Act 1: the setup.
    _add_meme(detective, "curiosity", 1)
    _add_meme(detective, "pride", 1)
    world.say(
        f"{detective.label} was a small detective who liked sharp clues and clean answers."
    )
    world.say(
        f"One morning, {detective.label} went to {setting.place} and noticed the entry right away."
    )
    world.say(setting.detail or f"The entry looked busy, with people coming and going.")

    # Act 2: the misunderstanding.
    world.para()
    _add_meme(detective, "suspicion", 1)
    _add_meme(detective, "worry", 1)
    world.say(
        f"At the entry, {detective.label} spotted {nudist.label}, who was a nudist, and stopped short."
    )
    world.say(
        f"{detective.label} thought, 'This looks like a problem.'"
    )
    world.say(
        f"Then {detective.label} saw {baba.label}, and the clues seemed even stranger."
    )

    # The detective tries a bad guess, then a better one.
    world.para()
    _add_meter(detective, "guessing", 1)
    world.say(
        f"{detective.label} first guessed that somebody had lost the right clothes at the entry."
    )
    world.say(
        f"But {detective.label} did not rush off. {detective.pronoun().capitalize()} looked again, one clue at a time."
    )

    # Act 3: problem solving.
    world.para()
    _add_meme(detective, "trust", 1)
    _add_meter(nudist, "calm", 1)
    world.say(
        f"{baba.label} smiled and explained that {nudist.label} was expected here."
    )
    world.say(
        f"The entry was for a place where people could come in safely, and {nudist.label} was not in trouble at all."
    )
    world.say(
        f"{detective.label} asked one more careful question, and the answer fit the clues."
    )
    _add_meter(nudist, "explained", 1)
    propagate(world, narrate=True)

    world.para()
    _add_meme(detective, "relief", 1)
    _add_meme(detective, "joy", 1)
    world.say(
        f"{detective.label} nodded. The misunderstanding was solved."
    )
    world.say(
        f"At the end, {detective.label} waved at {nudist.label} and walked beside {baba.label} past the entry, feeling proud of the careful answer."
    )

    world.facts.update(
        detective=detective,
        baba=baba,
        nudist=nudist,
        setting=setting,
        params=params,
    )
    return world


SETTINGS = {
    "museum": Setting(
        place="the museum entry",
        afford_entry=True,
        detail="A bright sign pointed toward the entry, and the floor shone like it had just been swept.",
    ),
    "pool": Setting(
        place="the pool entry",
        afford_entry=True,
        detail="The entry had wet footprints, echoing splashes, and a line of towels nearby.",
    ),
    "park": Setting(
        place="the park entry",
        afford_entry=True,
        detail="The entry stood under a tree, with a path leading to the swings and benches.",
    ),
}

DETECTIVE_NAMES = ["Mina", "Toby", "Jules", "Nia", "Rafi", "Pia"]
BABA_NAMES = ["Baba Roni", "Baba Noor", "Baba Eli", "Baba Sami"]
NUDIST_NAMES = ["Mr. Cloud", "Ari", "Nico", "Lena", "Miro"]


KNOWLEDGE = {
    "entry": [
        (
            "What is an entry?",
            "An entry is a place where people come in or go out of a building or area.",
        )
    ],
    "nudist": [
        (
            "What is a nudist?",
            "A nudist is a person who likes to be without clothes in places where that is allowed.",
        )
    ],
    "baba": [
        (
            "Who is baba?",
            "Baba is a word many children use for a father or grandfather, or for a loving older helper.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when people first think the wrong thing about a situation.",
        )
    ],
    "problem solving": [
        (
            "What does problem solving mean?",
            "Problem solving means looking at clues, asking questions, and finding a good answer.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks carefully for clues and tries to figure out what is really happening.",
        )
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about an entry, a nudist, and baba.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--baba-name")
    ap.add_argument("--nudist-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    baba_name = args.baba_name or rng.choice(BABA_NAMES)
    nudist_name = args.nudist_name or rng.choice(NUDIST_NAMES)
    return StoryParams(
        place=place,
        detective_name=detective_name,
        detective_type=detective_type,
        baba_name=baba_name,
        nudist_name=nudist_name,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"].label
    return [
        f"Write a short detective story set at {f['setting'].place} about {detective}, baba, and a nudist.",
        "Tell a child-friendly mystery where a first impression turns out to be wrong.",
        "Write a story about careful clues, a misunderstanding, and a kind explanation at an entry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    baba: Entity = f["baba"]
    nudist: Entity = f["nudist"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {detective.label} notice the mystery?",
            answer=f"{detective.label} noticed it at {setting.place}, right by the entry.",
        ),
        QAItem(
            question=f"Why did {detective.label} think something was wrong at first?",
            answer=f"{detective.label} saw {nudist.label}, who was a nudist, and first guessed the scene was a problem.",
        ),
        QAItem(
            question=f"Who helped solve the misunderstanding?",
            answer=f"{baba.label} helped by explaining the situation and showing that {nudist.label} was allowed to be there.",
        ),
        QAItem(
            question=f"What did {detective.label} do to solve the problem?",
            answer=f"{detective.label} slowed down, looked at the clues again, and asked careful questions until the answer fit.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        for q, a in pairs:
            out.append(QAItem(question=q, answer=a))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
detective_at_entry(detective) :- person(detective), sees_entry(detective).
misunderstanding(D) :- detective(D), suspicion(D), nudist_present, baba_present.
solved(D) :- detective(D), asks_questions(D), baba_explains, nudist_explained.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("sees_entry", "detective"))
    lines.append(asp.fact("person", "detective"))
    lines.append(asp.fact("detective", "detective"))
    lines.append(asp.fact("nudist_present"))
    lines.append(asp.fact("baba_present"))
    lines.append(asp.fact("suspicion", "detective"))
    lines.append(asp.fact("asks_questions", "detective"))
    lines.append(asp.fact("baba_explains"))
    lines.append(asp.fact("nudist_explained"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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
    StoryParams(
        place="museum",
        detective_name="Mina",
        detective_type="girl",
        baba_name="Baba Noor",
        nudist_name="Mr. Cloud",
    ),
    StoryParams(
        place="pool",
        detective_name="Toby",
        detective_type="boy",
        baba_name="Baba Roni",
        nudist_name="Ari",
    ),
    StoryParams(
        place="park",
        detective_name="Jules",
        detective_type="girl",
        baba_name="Baba Sami",
        nudist_name="Nico",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world keeps its reasoner compact and Python-led.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.detective_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
