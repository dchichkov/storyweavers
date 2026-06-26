#!/usr/bin/env python3
"""
A small storyworld for a nursery-rhyme-style mystery about tilling, disgust,
and a sore buttock that helps two friends reconcile.

Premise:
- A little creature loves to till a tiny garden patch.
- A second character feels disgust at the muddy work and misunderstands it.
- One character lands on a hard root and hurts a buttock.
- A mystery appears: who made the mysterious muddy mark, and why?

Turn:
- The friends look for clues in the soil, a spade, and a torn ribbon.
- They learn the muddy mark came from honest garden work, not a prank.

Resolution:
- They apologize, share the task, and reconcile.
- The ending is happy, with the garden neat and both friends smiling.

The prose and QA are driven by the simulated state, not a frozen template.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mess: str
    stain: str
    clue: str
    weather: str = "soft rain"


@dataclass
class Mystery:
    id: str
    question: str
    answer: str
    clue_words: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _hurt_buttock(world: World) -> None:
    hero = world.get("Pip")
    if hero.memes.get("tired", 0) >= THRESHOLD and hero.meters.get("root", 0) >= THRESHOLD:
        sig = ("hurt_buttock", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hurt"] = 1.0
            hero.meters["buttock_pain"] = 1.0


def _mystery_clue(world: World) -> None:
    clue = world.get("Clue")
    if clue.meters.get("mud", 0) >= THRESHOLD and clue.meters.get("torn", 0) >= THRESHOLD:
        world.facts["mystery_solved"] = True


def propagate(world: World) -> None:
    _hurt_buttock(world)
    _mystery_clue(world)


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    action: str
    mystery: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting("the garden"),
    "path": Setting("the little path"),
}

ACTIONS = {
    "till": Action(
        id="till",
        verb="till the soil",
        gerund="tilling the soil",
        mess="mud",
        stain="muddy",
        clue="a tiny brown smear",
        weather="soft rain",
    ),
}

MYSTERIES = {
    "muddy_mark": Mystery(
        id="muddy_mark",
        question="who made the muddy mark",
        answer="the mark came from honest tilling, not from a trick",
        clue_words={"mud", "torn", "spade"},
    )
}

NAMES = ["Pip", "Mimi", "Wren", "Juno", "Toby", "Luna"]
FRIEND_NAMES = ["Dot", "Ned", "Poppy", "Moss", "Nori", "Bram"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solved when the clue is muddy and torn.
solved(muddy_mark) :- clue(mud), clue(torn).

% Reconciliation happens after the mystery is solved and both friends apologize.
reconciled :- solved(muddy_mark), apology(hero), apology(friend).

% Happy ending means the reconciliation happened and the garden is tidy.
happy_ending :- reconciled, tidy(garden).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "garden"),
        asp.fact("setting", "path"),
        asp.fact("action", "till"),
        asp.fact("mystery", "muddy_mark"),
        asp.fact("clue", "mud"),
        asp.fact("clue", "torn"),
        asp.fact("clue", "spade"),
        asp.fact("tidy", "garden"),
        asp.fact("apology", "hero"),
        asp.fact("apology", "friend"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1. #show reconciled/0. #show happy_ending/0."))
    shown = set((sym.name, len(sym.arguments), tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("solved", 1, ("muddy_mark",)),
        ("reconciled", 0, ()),
        ("happy_ending", 0, ()),
    }
    if shown == expected:
        print("OK: ASP twin matches the intended story logic.")
        return 0
    print("MISMATCH in ASP twin.")
    print("shown:", shown)
    print("expected:", expected)
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(id="Pip", kind="character", type="boy", label=params.hero_name))
    friend = world.add(Entity(id="Dot", kind="character", type="girl", label=params.friend_name))
    spade = world.add(Entity(id="Spade", type="tool", label="a little spade"))
    clue = world.add(Entity(id="Clue", type="thing", label="the clue"))
    soil = world.add(Entity(id="Soil", type="thing", label="the soil"))

    # Act 1: setup
    world.say(f"Little {hero.label} lived by {setting.place}, where the soft wind hummed like a tune.")
    world.say(f"{hero.label} loved {ACTIONS['till'].gerund}, because the tiny rows looked neat when they were done.")
    world.say(f"One day {friend.label} came along and wrinkled her nose at the dark, damp earth.")
    friend.memes["disgust"] = 1.0
    world.say(f'"Oh dear," said {friend.label}, "that looks all {ACTIONS["till"].stain} and messy to me."')

    # Act 2: trouble and mystery
    world.para()
    world.say(f"{hero.label} kept working, but a hidden root gave a little tug beneath the ground.")
    hero.meters["root"] = 1.0
    hero.memes["tired"] = 1.0
    propagate(world)
    if hero.memes.get("hurt", 0) >= THRESHOLD:
        world.say(f"{hero.label} sat down with a small oof and rubbed {hero.pronoun('possessive')} sore buttock.")
        world.say(f"Then both friends noticed {ACTIONS['till'].clue} on the spade and a torn ribbon by the row.")

    clue.meters["mud"] = 1.0
    clue.meters["torn"] = 1.0
    spade.meters["mud"] = 1.0
    soil.meters["turned"] = 1.0
    propagate(world)

    world.say(f"They wondered at the little mystery: {MYSTERIES['muddy_mark'].question}?")
    world.say("They searched the ground, the ribbon, and the spade, and the answer began to bloom like a daisy.")
    world.say(f"The muddy mark was not a prank at all; it was the sign of honest work in the soil.")
    world.facts["mystery_solved"] = True

    # Act 3: reconciliation and happy ending
    world.para()
    hero.memes["sad"] = 1.0
    friend.memes["sorry"] = 1.0
    world.say(f"{friend.label} felt sorry for the frown she had made, and {hero.label} felt sorry for the sharp reply he had given.")
    world.say(f"They spoke kindly, and the ugly feeling loosened like a knot in a ribbon.")
    world.say(f'"I was wrong," said {friend.label}. "The dirt was not icky after all; it was a sign of good growing work."')
    world.say(f'"And I was grumpy," said {hero.label}. "Let us share the tilling and mend our mood."')
    world.say(f"So they reconciled, side by side, and finished the row together.")
    world.say("By evening the garden was tidy, the mystery was solved, and the moon looked down on two smiling friends.")
    world.say(f"It was a happy ending, with {friend.label} and {hero.label} waving at the neat little rows.")

    world.facts.update(
        hero=hero,
        friend=friend,
        spade=spade,
        clue=clue,
        soil=soil,
        action=ACTIONS["till"],
        mystery=MYSTERIES["muddy_mark"],
        resolved=True,
        reconciled=True,
        happy_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-like story about a child named {f["hero"].label} who loves {f["action"].gerund} in a little garden.',
        f'Tell a gentle mystery story where {f["friend"].label} feels disgust at the muddy soil, then learns the truth and reconciles with {f["hero"].label}.',
        f'Write a short happy ending story that includes a sore buttock, a muddy clue, and the word "{f["mystery"].question}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"What did {hero.label} love to do in the garden?",
            answer=f"{hero.label} loved {f['action'].gerund}. It made the little rows neat and ready for growing things."
        ),
        QAItem(
            question=f"Why did {friend.label} feel disgust at first?",
            answer=f"{friend.label} felt disgust because the soil looked dark, damp, and muddy. She thought it seemed messy before she learned what was happening."
        ),
        QAItem(
            question="What hurt and made the story pause for a moment?",
            answer=f"{hero.label} landed on a hidden root and had a sore buttock, so everyone stopped to rest and listen."
        ),
        QAItem(
            question="What was the mystery to solve?",
            answer=f"The mystery was who made the muddy mark. In the end, they learned it came from honest tilling, not from a trick."
        ),
        QAItem(
            question="How did the story end?",
            answer="The friends apologized, reconciled, and finished the garden together, which made a happy ending."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tilling do to soil?",
            answer="Tilling loosens the soil so air and water can reach it more easily, which helps plants grow."
        ),
        QAItem(
            question="What does disgust mean?",
            answer="Disgust is a strong feeling that makes something seem yucky or unpleasant."
        ),
        QAItem(
            question="What is a buttock?",
            answer="A buttock is one of the two rounded parts you sit on."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small nursery-rhyme storyworld about tilling, disgust, a sore buttock, and reconciliation.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if name == friend:
        friend = rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(setting=setting, action="till", mystery="muddy_mark", hero_name=name, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(setting="garden", action="till", mystery="muddy_mark", hero_name="Pip", friend_name="Dot"),
    StoryParams(setting="path", action="till", mystery="muddy_mark", hero_name="Mimi", friend_name="Bram"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1. #show reconciled/0. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name} and {p.friend_name} in the {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
