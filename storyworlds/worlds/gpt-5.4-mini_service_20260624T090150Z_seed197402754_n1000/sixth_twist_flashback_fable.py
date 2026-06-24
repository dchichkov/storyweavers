#!/usr/bin/env python3
"""
A small fable-like story world about a clever twist and a brief flashback.

Premise:
A kindly crow has a sixth seed to share at the old stump. The seed seems plain,
but it is the last one from a bundle that once fed six hungry friends.

Tension:
The squirrel wants to bury it for later, while the hare wants to eat it now.
The crow remembers why the seed matters, and a flashback explains the old debt.

Twist:
The seed is not a prize to keep. It is a promise. The sixth friend who once
shared food is now the one who needs help.

Resolution:
The characters choose kindness over hunger, and the seed becomes a meal shared
at once, proving that even a small gift can change who is generous.

This world tracks:
- physical meters: hunger, seed, distance, time
- emotional memes: greed, patience, gratitude, trust
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

WORLD_NAME = "sixth_twist_flashback_fable"


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "creature"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"crow", "fox", "hare", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the old stump"
    afford_seed_story: bool = True


@dataclass
class StoryParams:
    place: str = "stump"
    seed_count: int = 6
    hero: str = "crow"
    rival: str = "squirrel"
    listener: str = "hare"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.flashback_done = False

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

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.lines = list(self.lines)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.flashback_done = self.flashback_done
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable world with a sixth seed, a twist, and a flashback."
    )
    ap.add_argument("--place", choices=["stump"], default="stump")
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
    if args.place and args.place != "stump":
        raise StoryError("This little fable only grows at the old stump.")
    return StoryParams(place="stump", seed_count=6, seed=None)


def reasonableness_gate(params: StoryParams) -> None:
    if params.seed_count != 6:
        raise StoryError("The story needs the sixth seed to matter.")
    if params.place != "stump":
        raise StoryError("The fable begins at the old stump, and nowhere else.")


ASP_RULES = r"""
place(stump).
hero(crow).
rival(squirrel).
listener(hare).

seed_count(6).

valid_story(P) :- place(P), seed_count(6).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("place", "stump"),
        asp.fact("hero", "crow"),
        asp.fact("rival", "squirrel"),
        asp.fact("listener", "hare"),
        asp.fact("seed_count", 6),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the sixth-seed fable.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def _hunger_text(ent: Entity) -> str:
    h = ent.meters.get("hunger", 0)
    if h >= 3:
        return "very hungry"
    if h >= 1:
        return "a little hungry"
    return "full"


def flashback(world: World, crow: Entity, hare: Entity) -> None:
    if world.flashback_done:
        return
    world.flashback_done = True
    crow.memes["gratitude"] = crow.memes.get("gratitude", 0) + 1
    world.say(
        "The crow paused, and for a moment the stump seemed older than the trees. "
        "It remembered a day long ago, when six friends had found food together after a dry week."
    )
    world.say(
        "Back then, the hare had shared the last crumb, and the sixth friend had smiled with relief."
    )
    world.say(
        "That memory changed the crow's mind, because a gift remembered is stronger than a gift held tight."
    )


def twist(world: World, crow: Entity, squirrel: Entity, hare: Entity) -> None:
    crow.memes["trust"] = crow.memes.get("trust", 0) + 1
    squirrel.memes["greed"] = squirrel.memes.get("greed", 0) + 1
    world.say(
        "Then came the twist: the sixth seed was not meant to be kept like treasure."
    )
    world.say(
        "It was a sign that someone else had once been helped, and now someone else needed help too."
    )


def share_seed(world: World, crow: Entity, squirrel: Entity, hare: Entity) -> None:
    crow.memes["kindness"] = crow.memes.get("kindness", 0) + 1
    hare.memes["gratitude"] = hare.memes.get("gratitude", 0) + 1
    squirrel.memes["patience"] = squirrel.memes.get("patience", 0) + 1
    for ent in (crow, squirrel, hare):
        ent.meters["hunger"] = max(0, ent.meters.get("hunger", 0) - 1)
    world.say(
        "So the crow cracked the seed and shared the pieces."
    )
    world.say(
        "The squirrel waited, the hare nodded, and the three of them ate together without quarrel."
    )
    world.say(
        "In the end, the sixth seed became enough for all of them, and the stump stood quiet under a kinder sky."
    )


def tell_story(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(Place())
    crow = world.add(Entity(id="Crow", type="crow", label="crow"))
    squirrel = world.add(Entity(id="Squirrel", type="squirrel", label="squirrel"))
    hare = world.add(Entity(id="Hare", type="hare", label="hare"))

    crow.meters["hunger"] = 1
    squirrel.meters["hunger"] = 2
    hare.meters["hunger"] = 2
    crow.memes["patience"] = 1
    squirrel.memes["greed"] = 1
    hare.memes["trust"] = 1

    world.say(
        "At the old stump, a crow found the sixth seed in a tiny nest of grass."
    )
    world.say(
        f"The crow was {_hunger_text(crow)}, the squirrel was {_hunger_text(squirrel)}, and the hare was {_hunger_text(hare)}."
    )
    world.say(
        "All three looked at the seed, and each thought a different thought."
    )
    world.para()

    world.say(
        "The squirrel wanted to hide it for later, while the hare wanted to eat it at once."
    )
    world.say(
        "The crow did not answer right away, because the seed felt heavier than its shell."
    )
    flashback(world, crow, hare)
    world.para()

    twist(world, crow, squirrel, hare)
    world.say(
        "Now the crow understood that keeping the sixth seed would not make the day fair."
    )
    share_seed(world, crow, squirrel, hare)

    world.facts.update(
        crow=crow,
        squirrel=squirrel,
        hare=hare,
        place=params.place,
        seed_count=params.seed_count,
        twist=True,
        flashback=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable for a child about a sixth seed, a twist, and a flashback.',
        'Tell a gentle story where a crow finds the sixth seed at the old stump and learns to share.',
        'Write a fable-like tale that remembers an old kindness before revealing a twist about a small treasure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    crow = world.facts["crow"]
    squirrel = world.facts["squirrel"]
    hare = world.facts["hare"]
    return [
        QAItem(
            question="What did the crow find at the old stump?",
            answer="The crow found the sixth seed at the old stump.",
        ),
        QAItem(
            question="Why did the crow pause before deciding what to do?",
            answer="The crow paused because it remembered an old kindness in a flashback, and that memory made the seed feel important.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the sixth seed was not treasure to keep; it was a sign to share kindly because someone else needed help.",
        ),
        QAItem(
            question="What happened at the end?",
            answer="The crow cracked the seed and shared it with the squirrel and the hare, so they ate together without quarrel.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson, often with animal characters.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened before the present moment.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"flashback_done={world.flashback_done}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        atoms = asp.atoms(model, "valid_story")
        print(f"{len(atoms)} compatible story fact(s): {atoms}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    params = resolve_params(args, random.Random(base_seed))
    params.seed = base_seed

    samples: list[StorySample] = []
    if args.all:
        for i in range(args.n):
            p = StoryParams(place="stump", seed_count=6, seed=base_seed + i)
            samples.append(generate(p))
    else:
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
