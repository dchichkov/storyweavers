#!/usr/bin/env python3
"""
Standalone storyworld: expand_ratatouille_cautionary_myth

A small cautionary myth about a kitchen ritual that goes wrong when a humble
ratatouille is asked to expand beyond its rightful pot.
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

STYLES = ("Myth",)
FEATURES = ("Cautionary",)


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Pot:
    name: str
    capacity: int
    secure: bool = True


@dataclass
class StoryParams:
    place: str = "the old kitchen"
    seed: Optional[int] = None
    name: str = "Nina"
    helper: str = "grandmother"
    caution_level: str = "high"


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.pot: Pot = Pot(name="iron pot", capacity=3)
        self.fired: set[str] = set()
        self.myth_warning = False
        self.expanded = False
        self.broken = False
        self.resolved = False

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
    ap = argparse.ArgumentParser(description="Cautionary myth about expand and ratatouille.")
    ap.add_argument("--place", default="the old kitchen")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"], default=None)
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
    name = args.name or rng.choice(["Nina", "Milo", "Ari", "Lia", "Toma", "Sera"])
    helper = args.helper or rng.choice(["grandmother", "father", "mother", "grandfather"])
    return StoryParams(place=args.place, seed=None, name=name, helper=helper, caution_level="high")


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("thing", "ratatouille"),
        asp.fact("thing", "pot"),
        asp.fact("thing", "warning"),
        asp.fact("thing", "lid"),
        asp.fact("feature", "cautionary"),
        asp.fact("style", "myth"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
warning_needed(ratatouille) :- feature(cautionary), style(myth).
dangerous_expand(ratatouille) :- warning_needed(ratatouille).
resolution(ratatouille) :- dangerous_expand(ratatouille).
#show warning_needed/1.
#show dangerous_expand/1.
#show resolution/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    want = {
        ("warning_needed", ("ratatouille",)),
        ("dangerous_expand", ("ratatouille",)),
        ("resolution", ("ratatouille",)),
    }
    if atoms == want:
        print("OK: ASP twin matches Python reasoner.")
        return 0
    print("MISMATCH:")
    print("python gate: ", want)
    print("clingo model:", atoms)
    return 1


def _warn(world: World, hero: Entity, helper: Entity, food: Entity) -> None:
    world.myth_warning = True
    world.say(
        f"In the old kitchen, {hero.id} heard a cautionary tale: "
        f'"Do not ask the ratatouille to expand beyond the pot," '
        f"said {helper.id}."
    )
    world.say(
        f'"If it grows too far, the lid will lift, the steam will rush out, '
        f'and the evening will remember your mistake."'
    )
    world.facts["warning"] = True
    world.facts["food"] = food
    world.facts["helper"] = helper
    world.facts["hero"] = hero


def _expand(world: World, hero: Entity, food: Entity) -> None:
    world.expanded = True
    food.meters["size"] = food.meters.get("size", 1) + 3
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"But {hero.id} wanted to expand the ratatouille, so the spoon stirred harder "
        f"and the vegetables climbed toward the rim."
    )


def _break(world: World, food: Entity) -> None:
    if food.meters.get("size", 0) > world.pot.capacity:
        world.broken = True
        world.pot.secure = False
        food.meters["spilled"] = 1
        world.say(
            f"The pot could not hold the swelling dish. The lid shook loose, and "
            f"ratatouille spilled like a red and gold river across the hearth."
        )


def _resolve(world: World, hero: Entity, helper: Entity, food: Entity) -> None:
    if world.broken:
        world.say(
            f"Then {helper.id} showed {hero.id} the wiser way: gather the spilled "
            f"ratatouille, lower the fire, and make only as much as the pot could keep."
        )
        world.say(
            f"{hero.id} listened. The kitchen grew quiet again, and the lesson stayed "
            f"with the smoke: some things are best when they do not expand beyond their bounds."
        )
        world.resolved = True
    else:
        world.say(
            f"The ratatouille stayed within the iron pot, and the kitchen kept its calm."
        )
        world.resolved = True


def tell(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.name, kind="character", label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper))
    food = world.add(Entity(id="ratatouille", kind="thing", label="ratatouille", phrase="a savory ratatouille"))
    lid = world.add(Entity(id="lid", kind="thing", label="lid", phrase="a copper lid"))
    world.facts["lid"] = lid

    world.say(
        f"In {world.place}, {hero.id} was young and proud, and the old kitchen "
        f"smelled of onions, tomato, and thyme."
    )
    world.say(
        f"Near the stove sat {food.phrase}, waiting in the iron pot like a tiny treasure."
    )
    world.para()

    _warn(world, hero, helper, food)
    _expand(world, hero, food)
    _break(world, food)
    world.para()
    _resolve(world, hero, helper, food)

    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short Myth story with a Cautionary tone about a child who wants to expand ratatouille.',
        f"Tell a child-facing cautionary myth set in {world.place} where the ratatouille grows too large for the pot.",
        'Write a small myth in simple language that uses the words "expand" and "ratatouille".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    food: Entity = world.facts["food"]
    return [
        QAItem(
            question=f"Who wanted to expand the ratatouille?",
            answer=f"{hero.id} wanted to expand the ratatouille even after hearing the warning.",
        ),
        QAItem(
            question=f"Why did {helper.id} give a warning?",
            answer="Because the ratatouille might grow too big for the pot and spill over the rim.",
        ),
        QAItem(
            question="What happened when the dish grew too large?",
            answer="The lid shook loose and the ratatouille spilled across the hearth.",
        ),
        QAItem(
            question="What lesson did the story leave behind?",
            answer="It said that some good things are safer when they stay within their proper bounds.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ratatouille?",
            answer="Ratatouille is a cooked vegetable dish made from foods like tomatoes, zucchini, and peppers.",
        ),
        QAItem(
            question="What does expand mean?",
            answer="Expand means to grow bigger or spread farther out.",
        ),
        QAItem(
            question="Why can a pot be useful in cooking?",
            answer="A pot holds food while it cooks so the food stays together and does not spill everywhere.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place}")
    lines.append(f"pot_capacity={world.pot.capacity}")
    lines.append(f"pot_secure={world.pot.secure}")
    lines.append(f"warning={world.myth_warning}")
    lines.append(f"expanded={world.expanded}")
    lines.append(f"broken={world.broken}")
    lines.append(f"resolved={world.resolved}")
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="the old kitchen", name="Nina", helper="grandmother"),
            StoryParams(place="the old kitchen", name="Milo", helper="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
