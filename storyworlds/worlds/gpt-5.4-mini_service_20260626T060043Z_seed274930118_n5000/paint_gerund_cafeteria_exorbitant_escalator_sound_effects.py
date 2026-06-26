#!/usr/bin/env python3
"""
Storyworld: escalator paint mission in a cafeteria-like station.

A child in a busy space-station cafeteria wants to paint a poster while
riding the escalator to the observation deck. The escalator makes the paint
drip, a price turns exorbitant, and a small twist changes the plan.
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
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    rider: str
    companion: str
    item: str
    snack: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    sounds: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.sounds = list(self.sounds)
        return w


RIDERS = ["Nova", "Pip", "Tara", "Milo", "Zed", "Iris"]
COMPANIONS = ["the robot attendant", "a big sister", "a friendly pilot", "a dad in a visor"]
ITEMS = {
    "poster": Entity(id="poster", label="poster", phrase="a shiny poster", type="poster"),
    "cape": Entity(id="cape", label="cape", phrase="a bright cape", type="cape"),
    "patch": Entity(id="patch", label="patch", phrase="a painted patch", type="patch"),
}
SNACKS = ["spicy soup", "starlight noodles", "moon pie", "orange juice"]

ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

valid(Rider, Item) :- rider(Rider), item(Item), can_paint(Item).
valid_story(Rider, Item, Snack) :- valid(Rider, Item), snack(Snack), asks_for(Snack).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in RIDERS:
        lines.append(asp.fact("rider", r))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
        lines.append(asp.fact("can_paint", i))
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
    lines.append(asp.fact("asks_for", "moon pie"))
    lines.append(asp.fact("asks_for", "orange juice"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((r, i) for r in RIDERS for i in ITEMS)
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure style escalator story world.")
    ap.add_argument("--name", choices=RIDERS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--item", choices=list(ITEMS))
    ap.add_argument("--snack", choices=SNACKS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, i, s) for r in RIDERS for i in ITEMS for s in SNACKS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.name:
        combos = [c for c in combos if c[0] == args.name]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.snack:
        combos = [c for c in combos if c[2] == args.snack]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    rider, item, snack = rng.choice(combos)
    return StoryParams(
        rider=rider,
        companion=args.companion or rng.choice(COMPANIONS),
        item=item,
        snack=snack,
    )


def sound_effect(kind: str) -> str:
    return {
        "escalator": "Whirr-zzzz!",
        "drip": "Drip! Plip!",
        "price": "BEEP-BEEP!",
        "twist": "Krrrk!",
    }[kind]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What did {f['rider']} want to do with the {f['item']}?",
            answer=f"{f['rider']} wanted to paint the {f['item']} while riding the escalator.",
        ),
        QAItem(
            question=f"Why did the cafeteria clerk say the price was exorbitant?",
            answer="Because the paint splashed onto the snack machine sign and the repair fee was huge.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The escalator stopped at the snack level, and the child painted a new sign instead of the poster.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving staircase that carries people between levels.",
        ),
        QAItem(
            question="What does exorbitant mean?",
            answer="Exorbitant means far too expensive.",
        ),
        QAItem(
            question="Why are sound effects useful in stories?",
            answer="Sound effects help readers hear exciting moments, like a whirr, drip, or beep.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Space Adventure-style story about {f["rider"]} on an escalator in a cafeteria.',
        f'Include the words "paint", "cafeteria", and "exorbitant", plus a twist and sound effects.',
        f"Tell a child-friendly story where a moving escalator changes a paint plan into a surprise ending.",
    ]


def generate_world(params: StoryParams) -> World:
    w = World()
    rider = w.add(Entity(id=params.rider, kind="character", label=params.rider, type="child"))
    companion = w.add(Entity(id="companion", kind="character", label=params.companion, type="helper"))
    item = w.add(Entity(id=params.item, label=params.item, phrase=ITEMS[params.item].phrase))
    snack = w.add(Entity(id=params.snack, label=params.snack, phrase=params.snack))
    w.facts.update(rider=rider.id, companion=companion.label, item=item.label, snack=snack.label)

    w.say(f"{rider.id} stood at the top of the station escalator in the cafeteria and looked at {item.phrase}.")
    w.say(f"{sound_effect('escalator')} went the moving steps as {rider.id} held a little paint brush like a star wand.")
    w.say(f"{rider.id} wanted to paint the {item.label}, because the blank surface looked lonely.")
    w.para()
    w.say(f"But the escalator tilted and swayed, and {sound_effect('drip')} went the paint.")
    w.say(f"Blue drops dotted the cafeteria menu, and the clerk gasped that the cleanup fee was exorbitant.")
    w.say(f"{sound_effect('price')} flashed the register, as if it had seen a comet made of coins.")
    w.para()
    w.say(f"{companion.label} pointed to the landing below and grinned.")
    w.say(f"Then came the twist: the escalator stopped at the snack level, right beside the sign for {snack.label}.")
    w.say(f"{rider.id} painted a bright new sign instead, and the little job made the whole cafeteria feel like a spaceport again.")
    w.say(f"By the end, the paint stayed where it belonged, the bill was not exorbitant anymore, and {rider.id} rode down smiling.")
    w.sounds.extend([sound_effect("escalator"), sound_effect("drip"), sound_effect("price"), sound_effect("twist")])
    return w


def generate(params: StoryParams) -> StorySample:
    w = generate_world(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: {e.label or e.type}")
        print(f"sounds: {sample.world.sounds}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print()
        print("== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


CURATED = [
    StoryParams(rider="Nova", companion="the robot attendant", item="poster", snack="moon pie"),
    StoryParams(rider="Pip", companion="a friendly pilot", item="cape", snack="orange juice"),
    StoryParams(rider="Iris", companion="a big sister", item="patch", snack="starlight noodles"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
