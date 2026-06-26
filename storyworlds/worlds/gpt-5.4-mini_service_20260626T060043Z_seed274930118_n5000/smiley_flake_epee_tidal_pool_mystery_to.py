#!/usr/bin/env python3
"""
A heartwarming tiny story world set at a tidal pool, where Smiley and Flake
solve a small mystery, share, and deepen their friendship.
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
class Character:
    name: str
    role: str
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Object:
    name: str
    kind: str
    owner: Optional[str] = None
    found_by: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str = "tidal pool"
    hero: str = "Smiley"
    friend: str = "Flake"
    mystery: str = "epee"
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.characters: dict[str, Character] = {}
        self.objects: dict[str, Object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_character(self, c: Character) -> Character:
        self.characters[c.name] = c
        return c

    def add_object(self, o: Object) -> Object:
        self.objects[o.name] = o
        return o

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
        w = World(self.params)
        w.characters = copy.deepcopy(self.characters)
        w.objects = copy.deepcopy(self.objects)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


ASP_RULES = r"""
#show compatible/3.
place(tidal_pool).
character(smiley).
character(flake).
object(epee).
compatible(tidal_pool, mystery, sharing).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "tidal_pool"),
        asp.fact("character", "smiley"),
        asp.fact("character", "flake"),
        asp.fact("object", "epee"),
        asp.fact("feature", "mystery"),
        asp.fact("feature", "sharing"),
        asp.fact("feature", "friendship"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming mystery storyworld set in a tidal pool.")
    ap.add_argument("--place", choices=["tidal_pool"], default=None)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("tidal_pool", "mystery", "epee")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "tidal_pool":
        raise StoryError("This tiny world only lives in the tidal pool.")
    return StoryParams(place="tidal pool", seed=args.seed)


def solve_mystery(world: World) -> None:
    hero = world.characters["Smiley"]
    friend = world.characters["Flake"]
    item = world.objects["epee"]

    world.say(
        f"At the tidal pool, Smiley and Flake liked to listen to the waves "
        f"and peek into the little rock crannies."
    )
    world.say(
        f"Smiley noticed something shiny was missing: the tiny epee they used "
        f"for their make-believe sea captain games."
    )
    world.para()
    world.say(
        f"Flake looked under a shell, then behind a seaweed loop. "
        f"Smiley searched near a puddle where the tide had left sparkles behind."
    )
    hero.meter["worry"] = 1
    friend.meter["helpfulness"] = 1
    world.say(
        f"Neither one laughed at the mistake. Instead, they shared the searching "
        f"and kept going together."
    )
    item.owner = "Smiley"
    item.found_by = "Flake"
    world.para()
    world.say(
        f"At last, Flake found the epee tucked beside a smooth stone, where the "
        f"water had nudged it into a little nook."
    )
    world.say(
        f"Flake passed the epee to Smiley, and Smiley smiled so wide it looked "
        f"like a sunrise. Then Smiley shared the first turn with Flake, so they "
        f"both got to play sea captain."
    )
    hero.meme["joy"] = 2
    friend.meme["joy"] = 2
    hero.meme["friendship"] = 2
    friend.meme["friendship"] = 2
    world.say(
        f"The tidal pool felt warmer somehow, and the friends headed home with "
        f"their epee, their shells, and a bigger friendship than before."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        place="tidal pool",
        mystery="epee",
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming story set in a tidal pool where Smiley and Flake solve a small mystery.',
        'Tell a gentle friendship story that includes a lost epee, sharing, and a happy ending.',
        'Write a child-friendly story about friends at the tidal pool who search together and find what was missing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who were the friends in the story?",
            answer="The friends were Smiley and Flake.",
        ),
        QAItem(
            question="What was the mystery at the tidal pool?",
            answer="The mystery was where the little epee had gone.",
        ),
        QAItem(
            question="How did Smiley and Flake solve the mystery?",
            answer="They searched together, looked in little hiding places, and Flake found the epee near a smooth stone.",
        ),
        QAItem(
            question="What did they do after they found the epee?",
            answer="They shared it and both took turns playing, which made their friendship even stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a little pool of seawater left behind by the tide near rocks.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use or enjoy something too.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people care about each other and help each other.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for c in world.characters.values():
        lines.append(f"{c.name}: meter={c.meter} meme={c.meme}")
    for o in world.objects.values():
        lines.append(f"{o.name}: owner={o.owner} found_by={o.found_by} meter={o.meter} meme={o.meme}")
    return "\n".join(lines)


def generate_world(params: StoryParams) -> World:
    world = World(params)
    world.add_character(Character(name="Smiley", role="hero"))
    world.add_character(Character(name="Flake", role="friend"))
    world.add_object(Object(name="epee", kind="small shiny epee"))
    world.say(
        f"Smiley and Flake visited the tidal pool on a bright day full of tiny waves."
    )
    world.say(
        f"They came ready for a game, but Smiley soon noticed the epee was missing."
    )
    solve_mystery(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


CURATED = [StoryParams()]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
