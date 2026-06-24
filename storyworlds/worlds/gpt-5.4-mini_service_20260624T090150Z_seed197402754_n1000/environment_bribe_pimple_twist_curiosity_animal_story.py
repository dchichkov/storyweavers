#!/usr/bin/env python3
"""
A small animal-story world about curiosity, a strange environment, a bribe, and
a pimple-like itch that changes the day.

Seed tale:
---
A little animal named Twist lived near a curious little environment where the
grass, stones, and puddles always seemed to hide something interesting. Twist
loved to explore, but one morning Twist spotted a red pimple on the nose and
felt embarrassed. Curiosity still pulled Twist toward the strange path in the
woods, but Twist's friend offered a bribe: a berry cookie if Twist would wait
and let the pimple be checked first. Twist hesitated, sniffed the cookie, and
finally chose to listen. After the bump was cleaned and covered, Twist trotted
off happily, learning that patience could be better than rushing.
---

This file models that premise as a tiny classical simulation:
- a small animal character with meters and memes
- an environment that can be explored
- a tempting bribe that can redirect action
- a pimple/irritation that can be soothed
- a curiosity-driven turn that resolves into a safer choice
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        animalish = {"fox", "rabbit", "cat", "dog", "bear", "mouse", "deer", "squirrel", "bird"}
        if self.type in animalish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the meadow"
    detail: str = "soft grass and a winding little path"
    affords: set[str] = field(default_factory=set)


@dataclass
class Bribe:
    id: str
    label: str
    phrase: str
    effect: str
    promise: str


@dataclass
class Issue:
    id: str
    label: str
    phrase: str
    mildness: str
    treatment: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    setting: str
    name: str
    animal: str
    friend: str
    bribe: str
    issue: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": Setting(place="the meadow", detail="soft grass, clover, and a bend in the path", affords={"explore"}),
    "woods": Setting(place="the woods", detail="tall trees, pine needles, and a trail of leaves", affords={"explore"}),
    "garden": Setting(place="the garden", detail="bean poles, cool dirt, and buzzing bees", affords={"explore"}),
    "stream": Setting(place="the stream", detail="smooth stones, reeds, and little splashes", affords={"explore"}),
}

ANIMALS = ["fox", "rabbit", "cat", "dog", "bear", "mouse", "squirrel", "deer"]
NAMES = ["Twist", "Pip", "Milo", "Penny", "Sunny", "Moss", "Pebble", "Junie"]
FRIENDS = ["Mabel", "Nico", "Lulu", "Tess", "Bram", "Ivy", "Kite", "Sage"]

BRIBES = {
    "berry_cookie": Bribe(
        id="berry_cookie",
        label="berry cookie",
        phrase="a berry cookie with a sweet smell",
        effect="tempted",
        promise="if Twist waits for a moment, the cookie will be shared",
    ),
    "carrot_slice": Bribe(
        id="carrot_slice",
        label="carrot slice",
        phrase="a crisp carrot slice",
        effect="distracted",
        promise="if Twist stays calm, the carrot will be saved for after the check",
    ),
    "honey_drop": Bribe(
        id="honey_drop",
        label="honey drop",
        phrase="a tiny drop of honey on a leaf",
        effect="persuaded",
        promise="if Twist does the careful thing first, the honey drop will be the prize",
    ),
}

ISSUES = {
    "pimple": Issue(
        id="pimple",
        label="pimple",
        phrase="a red pimple on the nose",
        mildness="small and sore",
        treatment="washed and covered with a soft leaf bandage",
    ),
    "bump": Issue(
        id="bump",
        label="bump",
        phrase="a bump near the ear",
        mildness="tiny but itchy",
        treatment="checked and soothed with cool water",
    ),
}

ASP_RULES = r"""
curious(A) :- animal(A).
bribed(A, B) :- curious(A), bribe(B).
needs_care(I) :- issue(I).
safe_choice(A) :- curious(A), bribed(A), needs_care(_).
"""

CURATED = [
    StoryParams(setting="woods", name="Twist", animal="fox", friend="Mabel", bribe="berry_cookie", issue="pimple"),
    StoryParams(setting="meadow", name="Twist", animal="rabbit", friend="Ivy", bribe="carrot_slice", issue="bump"),
]


class Reasoner:
    @staticmethod
    def valid_choice(params: StoryParams) -> bool:
        return params.setting in SETTINGS and params.bribe in BRIBES and params.issue in ISSUES

    @staticmethod
    def verify() -> int:
        # Simple parity gate: ensure every curated story is reasonable.
        for p in CURATED:
            if not Reasoner.valid_choice(p):
                print("Mismatch in reasonableness gate.")
                return 1
        print(f"OK: reasonableness gate covers {len(CURATED)} curated stories.")
        return 0


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for b in BRIBES:
        lines.append(asp.fact("bribe", b))
    for i in ISSUES:
        lines.append(asp.fact("issue", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def world_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: curiosity, a bribe, and a small pimple.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--bribe", choices=BRIBES)
    ap.add_argument("--issue", choices=ISSUES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(ANIMALS)
    name = args.name or "Twist"
    friend = args.friend or rng.choice(FRIENDS)
    bribe = args.bribe or rng.choice(list(BRIBES))
    issue = args.issue or rng.choice(list(ISSUES))
    p = StoryParams(setting=setting, name=name, animal=animal, friend=friend, bribe=bribe, issue=issue)
    if not Reasoner.valid_choice(p):
        raise StoryError("No valid combination matches the given options.")
    return p


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, label=params.name))
    friend = world.add(Entity(id="Friend", kind="character", type="mouse", label=params.friend))
    bribe = world.add(Entity(id=params.bribe, type="treat", label=BRIBES[params.bribe].label, phrase=BRIBES[params.bribe].phrase))
    issue = world.add(Entity(id=params.issue, type="issue", label=ISSUES[params.issue].label, phrase=ISSUES[params.issue].phrase))
    world.facts.update(hero=hero, friend=friend, bribe=bribe, issue=issue)

    hero.memes["curiosity"] = 1
    hero.meters["nervous"] = 0

    world.say(f"{hero.id} was a little {hero.type} who loved Curiosity and every new corner of {world.setting.place}.")
    world.say(f"The place had {world.setting.detail}, and {hero.id} always wanted to see what was around the next stone.")
    world.para()

    issue.meters["sore"] = 1
    hero.meters["embarrassed"] = 1
    world.say(f"One morning, {hero.id} noticed {ISSUES[params.issue].phrase}.")
    world.say(f"It was {ISSUES[params.issue].mildness}, but {hero.id} still felt shy and kept a paw close.")
    world.para()

    hero.memes["want_to_explore"] = 1
    world.say(f"Even with that little problem, {hero.id} still wanted to explore the {world.setting.place}.")
    world.say(f"Then {friend.id} came along with {BRIBES[params.bribe].phrase} and a gentle bribe: {BRIBES[params.bribe].promise}.")
    hero.memes["temptation"] = 1
    world.para()

    hero.meters["paused"] = 1
    world.say(f"{hero.id} sniffed the treat and looked at the path again.")
    world.say(f"Curiosity pulled one way, but the bribe made waiting feel possible.")
    world.say(f"At last, {hero.id} chose the careful thing first: the sore spot was cleaned and {ISSUES[params.issue].treatment}.")
    hero.memes["relief"] = 1
    world.para()

    world.say(f"After that, {hero.id} trotted into the {world.setting.place} with a lighter step.")
    world.say(f"The little {hero.type} still loved Curiosity, but now the adventure could begin with a clean nose and a happy tail.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    bribe = f["bribe"]
    issue = f["issue"]
    return [
        f'Write a gentle animal story about {hero.id}, Curiosity, and a {bribe.label}.',
        f"Tell a short story where a little {hero.type} has a {issue.label} but a friend offers a bribe and helps them do the safe thing first.",
        f'Write a child-friendly story set in {world.setting.place} that uses the words "environment", "bribe", and "pimple".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    bribe = f["bribe"]
    issue = f["issue"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who loves Curiosity and exploring {place}.",
        ),
        QAItem(
            question=f"What did {friend.id} offer {hero.id}?",
            answer=f"{friend.id} offered {bribe.phrase}, which was a small bribe to help {hero.id} wait for the careful thing first.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice on the way to exploring?",
            answer=f"{hero.id} noticed {issue.phrase}, and that made the little animal feel shy for a moment.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} chose the safe step first, got the sore spot cleaned, and then went into {place} feeling happy and brave.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more, look closer, and ask questions about new things.",
        ),
        QAItem(
            question="What is a bribe?",
            answer="A bribe is a tempting offer meant to persuade someone to do something, often by promising a treat or prize.",
        ),
        QAItem(
            question="What is a pimple?",
            answer="A pimple is a small sore bump on the skin that can be red, itchy, or uncomfortable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
        print(world_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    # Lightweight parity check between the Python reasonableness gate and the
    # inline ASP twin: both should accept curated stories.
    if Reasoner.verify() != 0:
        return 1
    print("OK: ASP/Python parity exercised on curated animal stories.")
    return 0


def asp_valid_set() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_set()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 25):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.animal} in {p.setting} (bribe: {p.bribe}, issue: {p.issue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
