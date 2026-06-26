#!/usr/bin/env python3
"""
storyworlds/worlds/two_moral_value_inner_monologue_rhyming_story.py
===================================================================

A small standalone story world for a rhyming, child-facing moral tale with
inner monologue and a "two" seed word.

Premise:
- Two small characters want the same shiny thing.
- One feels the tug of taking it first.
- The world model tracks want, worry, honesty, sharing, and repair.
- A better choice changes the ending image.

The prose is authored to feel lightly rhythmic and gentle, while the state
drives what happens: desire can grow, a temptation can appear, a moral turn can
clear it, and the ending proves the change with concrete actions.
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

MORAL_GOODS = {
    "ball": ("a bright red ball", "ball"),
    "kite": ("a ribbon kite", "kite"),
    "book": ("a picture book", "book"),
    "bell": ("a tiny silver bell", "bell"),
}

PLACES = {
    "yard": ("the yard", "out in the yard"),
    "garden": ("the garden", "by the garden path"),
    "porch": ("the porch", "on the porch steps"),
    "park": ("the park", "near the grassy park"),
}

CHAR_NAMES = ["Mia", "Noah", "Luna", "Eli", "Tia", "Ben", "Zoe", "Max"]
TRAITS = ["brave", "gentle", "curious", "sweet", "busy", "tiny", "spry"]
FEELINGS = ["glad", "proud", "calm", "kind", "wobbly", "sour", "hopeful"]

ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

valid(Two, Prize) :- two(Two), prize(Prize), shared_ok(Two, Prize).

valid_story(Two, Prize, Moral) :- valid(Two, Prize), moral(Moral).

moral(kind).
moral(honest).
moral(sharing).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            gender = self.type
            if gender in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if gender in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    prize: str
    name1: str
    name2: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


class World:
    def __init__(self, place_key: str):
        self.place_key = place_key
        self.place, self.place_phrase = PLACES[place_key]
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming moral story world with two characters.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=MORAL_GOODS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--trait1")
    ap.add_argument("--trait2")
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


def asp_facts() -> str:
    import asp
    lines = []
    for pk in PLACES:
        lines.append(asp.fact("two", "two"))
        lines.append(asp.fact("place", pk))
    for pr in MORAL_GOODS:
        lines.append(asp.fact("prize", pr))
        lines.append(asp.fact("shared_ok", "two", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((("two", k) for k in MORAL_GOODS))
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    prize = args.prize or rng.choice(list(MORAL_GOODS))
    name1 = args.name1 or rng.choice(CHAR_NAMES)
    name2 = args.name2 or rng.choice([n for n in CHAR_NAMES if n != name1])
    trait1 = args.trait1 or rng.choice(TRAITS)
    trait2 = args.trait2 or rng.choice([t for t in TRAITS if t != trait1])
    return StoryParams(place=place, prize=prize, name1=name1, name2=name2, trait1=trait1, trait2=trait2)


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about two friends and "{f["prize_word"]}".',
        f"Tell a gentle moral tale where {f['name1']} and {f['name2']} both want the same shiny thing, then choose a kind way to share.",
        f"Write a small story with an inner monologue that helps a child choose honesty and sharing.",
    ]


def rhyme_end(word: str) -> str:
    return {
        "ball": "small",
        "kite": "bright",
        "book": "look",
        "bell": "well",
    }.get(word, "nice")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The two friends were {f['name1']} and {f['name2']}. They both wanted the same {f['prize_label']}.",
        ),
        QAItem(
            question=f"What did {f['name1']} think in their own mind before choosing what to do?",
            answer=(
                f"{f['name1']} had a little inner monologue: 'I want it now, but that would not be kind.' "
                f"That thought helped {f['name1']} choose a better way."
            ),
        ),
        QAItem(
            question=f"How did the story end for the {f['prize_label']}?",
            answer=(
                f"The {f['prize_label']} was shared between the two friends, so nobody felt left out. "
                f"They ended happy, and the ending felt light and bright."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something too, instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth and not pretending or sneaking when something matters.",
        ),
        QAItem(
            question="Why is a kind choice better than a greedy one?",
            answer="A kind choice helps everyone feel safe and happy, while a greedy choice can hurt feelings and cause trouble.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.kind:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


def build_story(world: World) -> None:
    f = world.facts
    n1, n2 = f["name1"], f["name2"]
    p = f["prize_label"]
    pl = f["place_phrase"]
    end_rhyme = rhyme_end(f["prize_word"])

    world.say(f"At {pl}, where the warm wind would softly blow, {n1} and {n2} came walking in a happy row.")
    world.say(f"They saw a {p} so bright and so neat, and both little hearts went patter-pat in a beat.")
    world.say(f"{n1} thought, \"I want it. Oh dear, I do.\" {n1} took a slow breath and looked at the blue sky too.")
    world.say(f"Then {n1} thought again, \"If I grab it alone, {n2} will feel sad, and that would not be home-sweet-home.\"")

    world.para()
    world.say(f"{n2} spoke up, with a voice like a chime: \"Let's take turns together; that feels just fine.\"")
    world.say(f"{n1} smiled and said, \"Yes, that's the way. We can both have fun in a fair, kind play.\"")
    world.say(f"So they shared the {p} and laughed in the light, each one taking a turn that felt just right.")

    world.para()
    world.say(f"By the end of the day, the sky looked {end_rhyme}, and their friendship felt steady, warm, and bright.")
    world.say(f"The {p} was still shining, but now it had a new glow: two happy friends and a moral to show.")
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = World(params.place)
    prize_phrase, prize_word = MORAL_GOODS[params.prize]
    world.add(Entity(id=params.name1, kind="character", type="girl", label=params.name1))
    world.add(Entity(id=params.name2, kind="character", type="boy", label=params.name2))
    world.add(Entity(id="prize", kind="thing", type=params.prize, label=params.prize, phrase=prize_phrase))
    world.facts.update(
        name1=params.name1,
        name2=params.name2,
        trait1=params.trait1,
        trait2=params.trait2,
        place=params.place,
        place_phrase=world.place_phrase,
        prize_label=params.prize,
        prize_word=prize_word,
    )
    build_story(world)
    return world


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(place="yard", prize="ball", name1="Mia", name2="Noah", trait1="gentle", trait2="brave"),
    StoryParams(place="garden", prize="kite", name1="Luna", name2="Eli", trait1="curious", trait2="sweet"),
    StoryParams(place="porch", prize="book", name1="Tia", name2="Ben", trait1="tiny", trait2="spry"),
]


def resolve_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible two/prize combos ({len(stories)} with moral tags):\n")
        for two, prize in combos:
            morals = sorted(m for (_, pr, m) in stories if pr == prize)
            print(f"  {two:4} {prize:8}  [{', '.join(morals)}]")
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
            params = resolve_from_args(args, random.Random(seed))
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
            header = f"### {p.name1} and {p.name2}: {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
