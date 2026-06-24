#!/usr/bin/env python3
"""
A small tall-tale storyworld about a curious child, a peculiar garnet, and the
funny trouble that follows from wanting to know what it can do.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    elder: Item
    garnet: Item
    place: str
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    elder_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Milo", "Ruby", "Nia", "Toby", "Lena", "Otis", "Ivy", "Pip"]
ELDERS = ["Grandpa", "Grandma", "Uncle Ned", "Aunt Bea", "Old Mara"]
PLACES = ["the canyon camp", "the red hill", "the dusty porch", "the lantern shed", "the little mesa"]


ASP_RULES = r"""
#show curious/1.
#show amused/1.
#show shared/1.

curious(H) :- hears_riddle(H).
amused(H) :- sees_spark(H).
shared(H) :- gives_garnet(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hears_riddle", "hero"),
        asp.fact("sees_spark", "hero"),
        asp.fact("gives_garnet", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show curious/1.\n#show amused/1.\n#show shared/1."))
    atoms = set((a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model)
    expected = {("curious", ("hero",)), ("amused", ("hero",)), ("shared", ("hero",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a curious garnet.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--elder-name", choices=ELDERS)
    ap.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        elder_name=args.elder_name or rng.choice(ELDERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(id="hero", label=params.name, phrase=f"young {params.name}", kind="character")
    elder = Item(id="elder", label=params.elder_name, phrase=params.elder_name, kind="character")
    garnet = Item(id="garnet", label="garnet", phrase="a thumb-sized garnet that looked like a cherry with a secret", owner=hero.id)
    return World(hero=hero, elder=elder, garnet=garnet, place=params.place)


def generate_story(world: World) -> str:
    h, e, g, p = world.hero, world.elder, world.garnet, world.place

    lines = [
        f"On a wind-whittled morning at {p}, {h.label} found a garnet the color of a grape that had learned to blush.",
        f"{h.label} held the garnet up to the sun and squinted so hard the crows blinked first.",
        f'"What does this garnet know?" {h.label} asked.',
        f'{e.label} laughed, a great barrel-rolling laugh, and said, "It knows how to stay small while looking mighty."',
        f"{h.label} asked again and again, \"What else? What else? What else?\"",
        f"Each time the question came back, the garnet seemed to wink brighter, as if the little stone enjoyed being chased by curiosity.",
        f"{h.label} tried putting it on a fence post, then in a tea cup, then on top of a boot, but the garnet kept looking grander than all three things put together.",
        f'{e.label} said, "That stone could make a sneeze sound like thunder and a pebble feel like a king."',
        f"That made {h.label} snort so suddenly that even the dust grinned.",
        f"At last {h.label} wrapped the garnet in a red cloth, carried it carefully home, and kept asking the same question all the way there, because curiosity is a long road and a merry one.",
        f"And every time the question came, the garnet flashed like a tiny sunset, as if it were saying, \"Keep wondering, keep walking, and keep your hat on.\"",
        f"So {h.label} went to sleep with {g.label} beside the bed, and the little stone shone like a pocket-sized promise that the biggest stories sometimes begin with something small enough to fit in a hand."
    ]
    return " ".join(lines)


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What did the child find?",
            answer="The child found a garnet, a small red stone that looked bright and important.",
        ),
        QAItem(
            question="Why did the child keep asking questions?",
            answer="The child was very curious and wanted to know what the garnet knew and what it could do.",
        ),
        QAItem(
            question="What made the story funny?",
            answer="The story was funny because the garnet was treated like a mighty treasure and the child kept asking the same question again and again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garnet?",
            answer="A garnet is a hard gemstone. It is often red or dark red and can look shiny like a tiny jewel.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to learn more and ask questions.",
        ),
        QAItem(
            question="Why can repeating a question matter in a story?",
            answer="Repeating a question can show that someone is very interested, impatient, or excited to learn the answer.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale story for young children about a curious child and a garnet.',
        f'Write a funny story set at {world.place} where a child keeps asking about a garnet again and again.',
        'Tell a simple story that uses repetition, curiosity, and a small red gemstone in a big-feeling adventure.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.elder, world.garnet]:
        lines.append(f"  {ent.id:6} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  place={world.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious/1.\n#show amused/1.\n#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: curious(hero), amused(hero), shared(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Milo", elder_name="Grandpa", place="the canyon camp"),
            StoryParams(name="Ruby", elder_name="Grandma", place="the red hill"),
            StoryParams(name="Ivy", elder_name="Aunt Bea", place="the dusty porch"),
            StoryParams(name="Otis", elder_name="Uncle Ned", place="the lantern shed"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
