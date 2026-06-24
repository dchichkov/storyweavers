#!/usr/bin/env python3
"""
A tiny storyworld: Sari and Pappy at the campground, where clumsy trouble
turns into kindness, reconciliation, and bravery in a nursery-rhyme style.
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
class Person:
    id: str
    role: str
    kind: str = "character"
    label: str = ""
    pronoun_subject: str = "they"
    pronoun_object: str = "them"
    pronoun_possessive: str = "their"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subj(self) -> str:
        return self.pronoun_subject

    def obj(self) -> str:
        return self.pronoun_object

    def pos(self) -> str:
        return self.pronoun_possessive


@dataclass
class Setting:
    place: str = "the campground"


@dataclass
class StoryParams:
    place: str = "campground"
    seed: Optional[int] = None
    name_child: str = "Sari"
    name_pappy: str = "Pappy"
    mishap: str = "clumsy"
    feature_kindness: str = "Kindness"
    feature_reconciliation: str = "Reconciliation"
    feature_bravery: str = "Bravery"


@dataclass
class World:
    setting: Setting
    people: dict[str, Person] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, person: Person) -> Person:
        self.people[person.id] = person
        return person

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld at the campground.")
    ap.add_argument("--place", choices=["campground"], default="campground")
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
    if args.place != "campground":
        raise StoryError("This tiny storyworld only knows the campground.")
    return StoryParams(place=args.place, seed=None)


ASP_RULES = r"""
% Nursery-rhyme world rules:
% If the child is clumsy, a small mishap happens.
mishap(clumsy).
feature(kindness).
feature(reconciliation).
feature(bravery).

% A kind act can heal a quarrel.
healed(X) :- feature(kindness), feature(reconciliation), feature(bravery), mishap(clumsy), story(X).

#show story/1.
#show feature/1.
#show mishap/1.
#show healed/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("story", "campground_nursery_rhyme"),
            asp.fact("place", "campground"),
            asp.fact("mishap", "clumsy"),
            asp.fact("feature", "kindness"),
            asp.fact("feature", "reconciliation"),
            asp.fact("feature", "bravery"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show healed/1."))
    healed = set(asp.atoms(model, "healed"))
    expected = {("campground_nursery_rhyme",)}
    if healed == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH: ASP parity failed.")
    print("  got:", sorted(healed))
    print("  expected:", sorted(expected))
    return 1


def make_world(params: StoryParams) -> World:
    w = World(setting=Setting(place="the campground"))
    sari = w.add(Person(
        id=params.name_child,
        role="child",
        pronoun_subject="she",
        pronoun_object="her",
        pronoun_possessive="her",
        label="a clumsy little camper",
    ))
    pappy = w.add(Person(
        id=params.name_pappy,
        role="elder",
        pronoun_subject="he",
        pronoun_object="him",
        pronoun_possessive="his",
        label="a kindly pappy",
    ))
    w.facts["sari"] = sari
    w.facts["pappy"] = pappy
    return w


def tell_story(w: World) -> None:
    sari = w.people["Sari"]
    pappy = w.people["Pappy"]

    sari.memes["joy"] = 1
    pappy.memes["warmth"] = 1

    w.say("At the campground, where pine trees sway, little Sari skipped in a merry way.")
    w.say("She loved the firelight, bright and small, and the singing crickets after dusk would call.")

    w.para()
    sari.memes["clumsy"] = 1
    sari.meters["bumped"] = 1
    pappy.memes["worry"] = 1
    w.say("But clumsy Sari tripped on a root and tumbled right down with a soft little hoot.")
    w.say("Her cup went rolling, her lantern swayed, and Pappy looked startled by the mess that was made.")

    w.para()
    pappy.memes["concern"] = 1
    sari.memes["sad"] = 1
    w.say('"Oh dear," said Pappy, "what shall we do?"')
    w.say('Then Sari said softly, "I am sorry to you."')
    sari.memes["kindness"] = 1
    pappy.memes["hurt"] = 0.0
    pappy.memes["forgiveness"] = 1
    w.say("She picked up the cup and the lantern too, and wiped up the spill as good campers do.")

    w.para()
    sari.memes["bravery"] = 1
    pappy.memes["pride"] = 1
    w.say("Then brave little Sari took one steady light and walked with Pappy through the dark of night.")
    w.say("Hand in hand they crossed the ground, and reconciliation softly hummed around.")
    w.say("By the campground fire, warm and near, they smiled together, calm and clear.")

    w.facts.update(
        conflict=True,
        resolved=True,
        kindness=True,
        reconciliation=True,
        bravery=True,
        mishap="clumsy",
        setting="campground",
    )


def story_prompts(world: World) -> list[str]:
    return [
        'Write a short nursery-rhyme-style story about Sari and Pappy at the campground.',
        'Tell a gentle tale where a clumsy mistake leads to kindness and reconciliation.',
        'Write a child-friendly story with bravery, a campground, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who was clumsy at the campground?",
            answer="Sari was clumsy at the campground, and her tumble started the trouble.",
        ),
        QAItem(
            question="What did Sari do after the mistake?",
            answer="She said she was sorry, picked up the spilled things, and helped make things tidy again.",
        ),
        QAItem(
            question="How did the story end?",
            answer="Sari and Pappy ended by walking together bravely and smiling in reconciliation by the fire.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone is gentle, helpful, and caring toward another person.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after a hurt or a disagreement.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being steady and doing the right thing even when something feels scary or hard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for p in world.people.values():
        meters = {k: v for k, v in p.meters.items() if v}
        memes = {k: v for k, v in p.memes.items() if v}
        lines.append(f"{p.id}: role={p.role} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [StoryParams(place="campground")]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show healed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show healed/1."))
        print("ASP model:")
        for a in model:
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        rng = random.Random(base_seed)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
