#!/usr/bin/env python3
"""
A small storyworld about imitation, kindness, and transformation, written in a
gentle rhyming style.

Seed premise:
A child watches a kind act, tries to imitate it, and is transformed by the
practice of kindness.
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
class Actor:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("joy", "kindness", "empathy", "calm", "grump", "pride", "confidence"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class KindAct:
    id: str
    action: str
    imitation: str
    rhyme: str
    effect: str
    trigger: str
    transform: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    name: str
    trait: str
    helper: str
    act: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Actor
    helper: Actor
    act: KindAct
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


ACTIONS = {
    "share": KindAct(
        id="share",
        action="share a cookie",
        imitation="share the next cookie",
        rhyme="share with care",
        effect="smiles grew bright like morning light",
        trigger="saw how sharing softened a frown",
        transform="went from grumbly to gentle",
        tags={"share", "kindness"},
    ),
    "help": KindAct(
        id="help",
        action="help pick up blocks",
        imitation="help pick up blocks",
        rhyme="help to build and help to heal",
        effect="the room felt warm and safe and sweet",
        trigger="watched a helping hand reach out",
        transform="turned from unsure to helpful",
        tags={"help", "kindness"},
    ),
    "comfort": KindAct(
        id="comfort",
        action="comfort a crying friend",
        imitation="bring a soft hug and kind words",
        rhyme="comfort, soften, brighten, blossom",
        effect="tears dried soon and a grin came through",
        trigger="heard a kind voice say, 'I'm here'",
        transform="shifted from shy to caring",
        tags={"comfort", "kindness"},
    ),
}


NAMES = ["Mia", "Leo", "Nora", "Finn", "Luna", "Theo", "Zoe", "Ava"]
TRAITS = ["small", "curious", "sour", "shy", "bright", "bouncy", "grumpy", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about kindness and imitation.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper", choices=NAMES)
    ap.add_argument("--act", choices=ACTIONS)
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
    act = args.act or rng.choice(list(ACTIONS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    if act == "comfort" and trait == "sour":
        pass
    return StoryParams(name=name, trait=trait, helper=helper, act=act)


def make_world(params: StoryParams) -> World:
    hero = Actor(id=params.name, type="child", traits=[params.trait])
    helper = Actor(id=params.helper, type="child", traits=["kind"])
    act = ACTIONS[params.act]
    w = World(hero=hero, helper=helper, act=act)
    hero.memes["grump"] = 1.0 if params.trait in {"sour", "grumpy"} else 0.0
    hero.memes["kindness"] = 0.0
    return w


def tell(world: World) -> None:
    h, k, act = world.hero, world.helper, world.act
    world.say(f"{h.id} was {h.traits[0]} and still as a cloud on a gray day.")
    world.say(f"Then {k.id} did {act.action}, and the room began to sway.")
    world.say(f"{h.id} watched that moment, light and clear, and wanted to do the same.")
    world.say(f"So {h.id} tried to imitate the deed, to join that kindling game.")
    world.say(f"{h.id} did {act.imitation}, and {act.effect}.")
    h.memes["kindness"] += 1.0
    h.memes["empathy"] += 1.0
    h.memes["grump"] = max(0.0, h.memes["grump"] - 1.0)
    h.memes["confidence"] += 1.0
    h.meters["joy"] += 1.0
    world.say(f"By the end, {h.id} had {act.transform}, and {act.rhyme}.")
    world.say(f"What began with imitation became transformation, warm and true as true can be.")


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short rhyming story about a child named {world.hero.id} who learns kindness by imitation.',
        f"Tell a gentle rhyming tale where {world.hero.id} watches {world.helper.id} do {world.act.action} and changes inside.",
        f"Write a child-friendly rhyme about kindness and transformation, ending with someone imitating a good deed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, k, act = world.hero, world.helper, world.act
    return [
        QAItem(
            question=f"Who tried to imitate the kind act in the story?",
            answer=f"{h.id} tried to imitate {k.id} and do {act.imitation} too.",
        ),
        QAItem(
            question=f"What did {k.id} do that {h.id} wanted to copy?",
            answer=f"{k.id} did {act.action}, and that made {h.id} want to copy the kindness.",
        ),
        QAItem(
            question="How did the child change by the end?",
            answer=f"{h.id} changed from {h.traits[0]} to more kind and confident after practicing the good deed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does imitate mean?",
            answer="To imitate means to watch someone and then do the same thing.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="A transformation is a change from one state to another, like becoming calmer or kinder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("act", aid))
        for t in sorted(act.tags):
            lines.append(asp.fact("tagged", aid, t))
    return "\n".join(lines)


ASP_RULES = r"""
good_act(A) :- act(A), tagged(A, kindness).
featured(A) :- good_act(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show featured/1."))
    clingo_set = set(asp.atoms(model, "featured"))
    python_set = {(aid,) for aid, act in ACTIONS.items() if "kindness" in act.tags}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} acts).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(clingo_set))
    print("PY :", sorted(python_set))
    return 1


def dump_trace(world: World) -> str:
    h = world.hero
    lines = ["--- trace ---"]
    lines.append(f"hero={h.id} traits={h.traits} meters={dict(h.meters)} memes={dict(h.memes)}")
    lines.append(f"helper={world.helper.id} action={world.act.id}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show featured/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show featured/1."))
        feats = sorted(set(asp.atoms(model, "featured")))
        print(f"{len(feats)} featured acts:")
        for (aid,) in feats:
            print(f"  {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", trait="grumpy", helper="Luna", act="share"),
            StoryParams(name="Leo", trait="sour", helper="Ava", act="help"),
            StoryParams(name="Nora", trait="shy", helper="Finn", act="comfort"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
