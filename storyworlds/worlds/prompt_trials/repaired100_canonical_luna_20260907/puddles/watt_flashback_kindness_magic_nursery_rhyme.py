#!/usr/bin/env python3
"""A tiny nursery-rhyme world about Watt, a kind flashback, and a little magic."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Watt"
    place: str = "the moonlit nursery"
    object: str = "a small silver bell"
    problem: str = "lost"
    seed: Optional[int] = None


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, actor: str, target: str, text: str,
               cause: str = "", result: str = "") -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    if not params.hero or not params.friend:
        raise StoryError("The story needs both a child and a helper.")
    world = World(params)
    luna = world.add(Entity("hero", "character", params.hero,
                            memes={"kindness": 1.0, "hope": 1.0}))
    watt = world.add(Entity("watt", "character", params.friend,
                            memes={"kindness": 1.0, "memory": 1.0}))
    bell = world.add(Entity("bell", "object", params.object,
                            meters={"lost": 1.0}))
    moon = world.add(Entity("moonbeam", "magic", "a silver moonbeam",
                            meters={"glow": 1.0}, memes={"magic": 1.0}))
    world.facts.update(hero=luna, friend=watt, bell=bell, moon=moon,
                       flashback=False, kindness=False, magic=False,
                       found=False)
    return world


def tell(world: World) -> None:
    p = world.params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    bell: Entity = world.facts["bell"]  # type: ignore[assignment]
    moon: Entity = world.facts["moon"]  # type: ignore[assignment]

    world.record(
        "arrival", hero.id, bell.id,
        f"In {p.place}, Luna heard a hush by the bed: “Oh, dear little bell, "
        f"where can you be?” The silver bell had slipped away, and the nursery "
        f"felt quiet as a cloud.",
        cause="The bell was missing from its little ribbon.",
        result="Luna began searching instead of settling down.",
    )

    world.para()
    world.turn += 1
    world.facts["flashback"] = True
    hero.memes["memory"] = 1.0
    world.record(
        "flashback", hero.id, friend.id,
        f"Then Luna remembered a flashback from yesterday: Watt had shared a "
        f"warm beam of light when Luna felt afraid. “Watt, you helped me then,” "
        f"Luna said. “Will you help me now?” Watt answered, “Kindness remembers "
        f"the way home.”",
        cause="Luna remembered Watt's earlier kindness.",
        result="She chose to search gently and invite Watt to help.",
    )

    world.para()
    world.turn += 1
    world.facts["kindness"] = True
    hero.memes["kindness"] += 1.0
    friend.memes["kindness"] += 1.0
    world.record(
        "kindness", friend.id, hero.id,
        f"Watt did not laugh at Luna's worry. He listened, then shared his "
        f"brightest glow beneath the rug. “You look there,” he said. “I’ll look "
        f"here.” Together they searched, tiptoe-tap, without blaming anyone.",
        cause="Watt answered Luna with patient kindness.",
        result="The friends searched together and made the dark places bright.",
    )

    world.para()
    world.turn += 1
    world.facts["magic"] = True
    moon.meters["glow"] += 1.0
    moon.memes["magic"] += 1.0
    bell.meters["lost"] = 0.0
    bell.meters["found"] = 1.0
    world.facts["found"] = True
    world.record(
        "magic", friend.id, bell.id,
        f"A moonbeam curled like a ribbon and gave one tiny wink. Magic made the "
        f"bell sparkle beneath the pillow. “There you are!” cried Luna. Watt "
        f"lifted it carefully, and the bell chimed, “Ding-ding, kindness wins!”",
        cause="Their shared kindness opened a small magical path of light.",
        result="The moonbeam revealed the lost bell beneath the pillow.",
    )

    world.para()
    world.turn += 1
    hero.memes["hope"] += 1.0
    world.record(
        "lullaby", hero.id, bell.id,
        f"Luna tied the bell back on its ribbon and hugged Watt. “A friend who "
        f"remembers and helps is a treasure,” she said. Watt glowed softly. "
        f"Then bell, beam, and friends sang a nursery rhyme: “Sleep now, moon; "
        f"shine now, star; kind hearts guide us near and far.”",
        cause="The bell was safe because Luna and Watt kept helping one another.",
        result="The nursery grew peaceful, and the friends rested beneath the glow.",
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a Nursery Rhyme story about {p.hero} and {p.friend} finding {p.object} "
        f"with a flashback, kindness, and magic.",
        f"Tell a gentle story in which a child remembers an earlier kindness and "
        f"uses it to solve a small problem in {p.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrival": "Why did Luna begin searching?",
        "flashback": "What did Luna remember about Watt?",
        "kindness": "How did Watt help?",
        "magic": "How was the bell found?",
        "lullaby": "How did the story end?",
    }
    return [
        QAItem(question=questions[event.kind],
               answer=f"{event.cause} {event.result}")
        for event in world.history
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a flashback?",
               "A flashback is a moment when someone remembers something that happened before."),
        QAItem("What is kindness?",
               "Kindness means helping, listening, and caring about another person's feelings."),
        QAItem("What is magic in a nursery rhyme?",
               "Magic is an imaginary wonder that helps the story sparkle and change."),
        QAItem("What is a watt?",
               "A watt is a unit used to measure how quickly energy is used."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: {entity.label}; meters={meters}; memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    story = world.render()
    sample = StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise StoryError("A generated story must retain its world.")
    if not world.facts["found"] or not world.facts["flashback"]:
        raise StoryError("The story must resolve through memory and discovery.")
    if "watt" not in sample.story.lower():
        raise StoryError("The story must include Watt.")
    if any(marker in sample.story for marker in ("{", "}", "__", "meters=", "memes=")):
        raise StoryError("Internal world details leaked into the story.")
    if len(sample.story_qa) != 5:
        raise StoryError("The story must provide five grounded answers.")
    for event in world.history:
        if event.text not in sample.story:
            raise StoryError("An event was not rendered in the story.")


ASP_RULES = r"""
found(Bell) :- flashback, kindness, magic, lost(Bell).
resolved :- found(Bell).
#show found/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("lost", "bell"),
        asp.fact("flashback"),
        asp.fact("kindness"),
        asp.fact("magic"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def verify_asp() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        found = asp.atoms(model, "found")
        resolved = asp.atoms(model, "resolved")
    except ImportError as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if found != [("bell",)] or resolved != [()]:
        print("ASP verification failed.")
        return 1
    sample = generate(StoryParams())
    check_sample(sample)
    print("OK: ASP and Python agree; generated story verified.")
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a nursery-rhyme story about Watt, memory, kindness, and magic."
    )
    parser.add_argument("--hero", default="Luna")
    parser.add_argument("--friend", default="Watt")
    parser.add_argument("--place", default="the moonlit nursery")
    parser.add_argument("--object", default="a small silver bell")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    if args.friend.strip().lower() != "watt":
        raise StoryError("The helper must be Watt so the story's watt motif remains clear.")
    return StoryParams(
        hero=args.hero,
        friend=args.friend,
        place=args.place,
        object=args.object,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify_asp())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program())
            print("ASP model:")
            for atom in model:
                print(f"  {atom}")
        except ImportError as exc:
            raise SystemExit(f"ASP unavailable: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for index in range(args.n if not args.all else 1):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### {sample.params.hero} and {sample.params.friend}" if args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
