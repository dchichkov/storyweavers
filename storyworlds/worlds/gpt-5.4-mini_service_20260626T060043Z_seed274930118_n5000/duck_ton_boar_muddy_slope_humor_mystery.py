#!/usr/bin/env python3
"""
A fairy-tale storyworld: a duck, a boar, and a muddy slope with a small mystery
to solve. The tale stays child-facing, lightly humorous, and state-driven: the
world model tracks the mud, the load of a ton of stones, and the clues that
help the characters discover what really happened on the hill.
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

HUMOR = "humor"
MYSTERY = "mystery"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    lost: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"duck"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boar"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.kind == "group" else "it"


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Della"
    boar_name: str = "Bram"
    place: str = "the muddy slope"
    load: str = "a ton of shiny pebbles"
    lost_item: str = "a brass bell"


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _mudslide(world: World) -> list[str]:
    out: list[str] = []
    duck = world.get("duck")
    boar = world.get("boar")
    load = world.get("load")
    if duck.meters.get("push", 0) >= 1 and boar.meters.get("slip", 0) >= 1 and "mudslide" not in world.fired:
        world.fired.add("mudslide")
        load.meters["muddy"] = 1
        duck.memes["surprise"] = duck.memes.get("surprise", 0) + 1
        boar.memes["embarrassment"] = boar.memes.get("embarrassment", 0) + 1
        out.append("The ton of pebbles slid with a silly swish and splattered mud on everyone.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        produced = _mudslide(world)
        if produced:
            changed = True
            for s in produced:
                world.say(s)


def tell(params: StoryParams) -> World:
    world = World()
    duck = world.add(Entity(id="duck", kind="character", type="duck", label=params.name))
    boar = world.add(Entity(id="boar", kind="character", type="boar", label=params.boar_name))
    load = world.add(Entity(id="load", type="load", label="the load", phrase=params.load))
    bell = world.add(Entity(id="bell", type="treasure", label="bell", phrase=params.lost_item, lost=True))

    duck.memes["curiosity"] = 1
    duck.memes["kindness"] = 1
    boar.memes["grump"] = 1
    world.facts.update(place=params.place, load=params.load, lost_item=params.lost_item)

    world.say(
        f"Once upon a time, a little duck named {duck.label} lived near {params.place}. "
        f"{duck.label} liked jokes, shiny things, and questions that begged to be solved."
    )
    world.say(
        f"On the hill below, a boar named {boar.label} grunted over {params.load}, "
        f"which was very heavy for such a wobbly path."
    )
    world.say(
        f"One misty morning, {boar.label} cried, 'My {params.lost_item} is gone!' "
        f"and the whole slope seemed to hold its breath."
    )

    world.para()
    world.say(
        f"{duck.label} peered into the mud and found a round print, then another. "
        f"They were too small for a boar and too tidy for a fox."
    )
    world.say(
        f"{duck.label} quacked, 'A mystery with muddy clues! This ought to be fun.' "
        f"{boar.label} blinked, because he had not expected a joke to begin an investigation."
    )

    world.para()
    duck.meters["push"] = 1
    boar.meters["slip"] = 1
    world.say(
        f"Together they nudged {params.load} aside to clear the path. "
        f"The slope was slick, and the pebbles rolled like laughing marbles."
    )
    propagate(world)
    world.say(
        f"Behind the stones, {duck.label} spotted {params.lost_item}, caught in a tuft of grass. "
        f"It had not been stolen at all; it had simply bounced downhill and waited politely."
    )

    world.para()
    boar.memes["relief"] = 1
    duck.memes["joy"] = 1
    world.say(
        f"{boar.label} snorted with relief, and even laughed at how serious he had looked "
        f"while chasing a bell that was only taking a nap in the mud."
    )
    world.say(
        f"{duck.label} tied the {params.lost_item} to a string, and the two friends marched home "
        f"with the ton of pebbles safely behind them, the slope shining with muddy tracks."
    )

    world.facts.update(duck=duck, boar=boar, load=load, bell=bell, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy tale for young children about a duck and a boar on a muddy slope, with a funny mystery about {f['lost_item']}.",
        f"Tell a humorous mystery where a duck solves a missing-object problem on {f['place']} while helping a boar move {f['load']}.",
        f"Write a short fairy tale with muddy tracks, a heavy load, and a happy discovery at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    duck: Entity = f["duck"]  # type: ignore[assignment]
    boar: Entity = f["boar"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery of the missing {f['lost_item']}?",
            answer=f"The duck named {duck.label} solved it by following the muddy clues on {f['place']}.",
        ),
        QAItem(
            question=f"What heavy thing was the boar trying to move on the slope?",
            answer=f"The boar was trying to move {f['load']}, which was a ton of pebbles.",
        ),
        QAItem(
            question=f"Where was the missing {f['lost_item']} found?",
            answer=f"It was found behind the stones, caught in a tuft of grass on the muddy slope.",
        ),
        QAItem(
            question=f"How did the story end for the duck and the boar?",
            answer=f"They laughed, recovered the bell, and went home together with the load safely behind them.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a muddy slope?",
        answer="A muddy slope is a hill with wet, slippery dirt that can make feet slide.",
    ),
    QAItem(
        question="What does a detective do in a mystery?",
        answer="A detective looks for clues and uses them to figure out what happened.",
    ),
    QAItem(
        question="Why can mud make a path funny and hard to walk on?",
        answer="Mud can be slippery and sticky, so people may slide or leave silly footprints.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: duck, boar, and a muddy-slope mystery.")
    ap.add_argument("--name")
    ap.add_argument("--boar-name")
    ap.add_argument("--place", default="the muddy slope")
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
    name = args.name or rng.choice(["Della", "Mina", "Pip", "Nora", "Lulu"])
    boar_name = args.boar_name or rng.choice(["Bram", "Tobin", "Moss", "Gor", "Porky"])
    place = args.place
    if "slope" not in place:
        raise StoryError("This world only supports the muddy slope setting.")
    return StoryParams(seed=None, name=name, boar_name=boar_name, place=place)


ASP_RULES = r"""
duck(d1).
boar(b1).
load(l1).
lost_item(i1).

on_slope(d1).
on_slope(b1).
on_slope(l1).

mystery(i1) :- lost_item(i1).
humor(d1) :- duck(d1).
humor(b1) :- boar(b1).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("duck", "d1"),
        asp.fact("boar", "b1"),
        asp.fact("load", "l1"),
        asp.fact("lost_item", "i1"),
        asp.fact("place", "muddy_slope"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show duck/1.\n#show boar/1.\n#show load/1.\n#show lost_item/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    want = {
        ("duck", ("d1",)),
        ("boar", ("b1",)),
        ("load", ("l1",)),
        ("lost_item", ("i1",)),
    }
    if atoms == want:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", sorted(atoms ^ want))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.lost:
            bits.append("lost=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show duck/1.\n#show boar/1.\n#show load/1.\n#show lost_item/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name="Della", boar_name="Bram", place="the muddy slope")
        samples.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
