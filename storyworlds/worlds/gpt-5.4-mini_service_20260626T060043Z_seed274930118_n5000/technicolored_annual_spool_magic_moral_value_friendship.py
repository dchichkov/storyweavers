#!/usr/bin/env python3
"""
A small comedy storyworld about a technicolored annual spool festival where
magic, moral value, and friendship shape the ending.
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
class StoryParams:
    name: str = "Pippa"
    friend: str = "Milo"
    place: str = "the annual spool fair"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
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


REGISTRY = {
    "place": "the annual spool fair",
    "spool": {
        "label": "technicolored spool",
        "phrase": "a technicolored spool of thread",
        "magic": True,
        "weight": 1,
    },
    "moral": {
        "label": "moral value",
        "phrase": "a lesson about sharing",
    },
    "friendship": {
        "label": "friendship ribbon",
        "phrase": "a friendship ribbon",
    },
}

PEOPLE = ["Pippa", "Milo", "Nina", "Toby", "Lina", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: technicolored annual spool magic.")
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--place", default=REGISTRY["place"])
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
    name = args.name or rng.choice(PEOPLE)
    friend = args.friend or rng.choice([p for p in PEOPLE if p != name])
    place = args.place or REGISTRY["place"]
    if name == friend:
        raise StoryError("The child and the friend must be different people.")
    return StoryParams(name=name, friend=friend, place=place)


def reasonableness_gate(params: StoryParams) -> None:
    if "spool" not in params.place.lower() and "fair" not in params.place.lower():
        raise StoryError("This story needs a spool-themed setting for the technicolored spool to matter.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World()
    child = world.add(Entity(id=params.name, kind="character", type="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type="friend"))
    spool = world.add(Entity(id="spool", kind="thing", type="spool"))
    ribbon = world.add(Entity(id="ribbon", kind="thing", type="ribbon"))
    lesson = world.add(Entity(id="lesson", kind="idea", type="moral"))

    child.memes["curiosity"] = 1
    child.memes["joy"] = 1
    friend.memes["joy"] = 1
    spool.meters["magic"] = 1
    ribbon.meters["bright"] = 1
    lesson.memes["value"] = 1

    world.say(
        f"Every year at {params.place}, {params.name} hunted for the most absurd prize of all: "
        f"the technicolored spool."
    )
    world.say(
        f"It shimmered like a rainbow that had swallowed a paint box, and {params.name} declared "
        f"it could surely fix any problem, even a grumpy one."
    )

    world.para()
    world.say(
        f"When {params.friend} arrived, both children reached for the spool at the same time and "
        f"nearly toppled into a basket of glittery buttons."
    )
    child.memes["conflict"] = 1
    friend.memes["conflict"] = 1
    world.say(
        f"The spool rolled under a bench, bounced off a lemonade sign, and stopped right beside "
        f"a note that read, \"Magic works better when shared.\""
    )
    lesson.memes["revealed"] = 1

    world.para()
    child.memes["generosity"] = 1
    friend.memes["trust"] = 1
    child.memes["conflict"] = 0
    friend.memes["conflict"] = 0
    world.say(
        f"{params.name} giggled, handed {params.friend} one end of the thread, and together they "
        f"used the technicolored spool to tie a cheerful banner over the snack table."
    )
    world.say(
        f"The banner spelled out the moral value of the day: sharing makes magic behave, and "
        f"friendship makes the joke land."
    )
    world.say(
        f"By sunset, {params.name} and {params.friend} were laughing under the new banner, while "
        f"the spool sat proudly in the middle like a tiny rainbow boss."
    )

    world.facts.update(
        name=params.name,
        friend=params.friend,
        place=params.place,
        spool=spool,
        ribbon=ribbon,
        lesson=lesson,
    )

    story_qa = [
        QAItem(
            question=f"What shiny thing did {params.name} want at {params.place}?",
            answer="It was the technicolored spool, a rainbow-bright spool of thread.",
        ),
        QAItem(
            question=f"What happened when {params.name} and {params.friend} both reached for it?",
            answer="They nearly toppled into a basket of glittery buttons, and the spool rolled away.",
        ),
        QAItem(
            question="What did the note say about magic?",
            answer="The note said that magic works better when shared.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{params.name} and {params.friend} shared the spool, tied up a banner, and laughed under it at sunset.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a spool?",
            answer="A spool is a round thing that holds thread or string so it can unwind neatly.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind, helping each other, and enjoying time together.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good lesson about how to treat people, like sharing or being honest.",
        ),
        QAItem(
            question="Why can magic be funny in a story?",
            answer="Magic can be funny when it causes surprising, silly trouble before helping fix the problem.",
        ),
    ]

    prompts = [
        "Write a funny story about a technicolored spool at an annual fair.",
        "Tell a comedy story where magic causes a small problem but friendship solves it.",
        "Write a child-friendly tale that ends with a moral value about sharing.",
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world trace ---")
        for ent in sample.world.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{ent.id}: {ent.kind}/{ent.type} {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
place(annual_spool_fair).
spool(technicolored_spool).
magic(technicolored_spool).
friendship(friendship_ribbon).
moral_value(lesson).

compatible_story(P) :- place(P), spool(technicolored_spool), magic(technicolored_spool),
                       friendship(friendship_ribbon), moral_value(lesson).
#show compatible_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "annual_spool_fair"),
            asp.fact("spool", "technicolored_spool"),
            asp.fact("magic", "technicolored_spool"),
            asp.fact("friendship", "friendship_ribbon"),
            asp.fact("moral_value", "lesson"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "compatible_story"))
    py = {("annual_spool_fair",)}
    if atoms == py:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", sorted(atoms), sorted(py))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible_story")))


def show_asp() -> None:
    print(asp_program())


def resolve_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.place = args.place or params.place
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        show_asp()
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story setting(s):")
        for s in stories:
            print(" ", s[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(name="Pippa", friend="Milo", place="the annual spool fair")),
            generate(StoryParams(name="Nina", friend="Owen", place="the annual spool fair")),
            generate(StoryParams(name="Lina", friend="Toby", place="the annual spool fair")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
