#!/usr/bin/env python3
"""
A small fable world about curiosity, a hoard, and moral value.

Seed tale:
A mouse found a hoard of shiny seeds hidden in an old wall. The mouse felt curious and wanted
to keep them all, even though a robin and a hedgehog had helped gather them. An atrocious storm
knocked the wall loose, and the seeds spilled everywhere. The mouse learned that sharing the hoard
and keeping promises mattered more than owning a pile alone.

The storyworld models:
- a small setting with one hidden hoard
- one curious hero
- a mutual-help relationship with another creature
- a moral choice between greed and fairness
- a turn where the hoard is damaged and redistributed
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "fox", "badger", "rabbit", "robin", "hedgehog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    count: int
    value: str


@dataclass
class Helper:
    id: str
    label: str
    type: str
    verb: str
    aid: str
    mutual_phrase: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    treasure: str
    seed: Optional[int] = None


SETTINGS = {
    "old_wall": Setting(place="the old wall", weather="windy", affords={"hide", "share", "spill"}),
    "orchard": Setting(place="the orchard", weather="breezy", affords={"hide", "share", "spill"}),
    "meadow": Setting(place="the meadow", weather="sunny", affords={"hide", "share", "spill"}),
}

TREASURES = {
    "seeds": Treasure(label="hoard of seeds", phrase="a hoard of shiny sunflower seeds", type="seeds", count=12, value="food"),
    "berries": Treasure(label="hoard of berries", phrase="a hoard of sweet berries", type="berries", count=9, value="food"),
    "coins": Treasure(label="hoard of coins", phrase="a hoard of bright copper coins", type="coins", count=8, value="trade"),
}

HELPERS = {
    "robin": Helper(id="robin", label="robin", type="robin", verb="helped gather", aid="picked up dropped pieces", mutual_phrase="shared the work"),
    "hedgehog": Helper(id="hedgehog", label="hedgehog", type="hedgehog", verb="helped carry", aid="bumped loose pieces into a pile", mutual_phrase="shared the work"),
    "rabbit": Helper(id="rabbit", label="rabbit", type="rabbit", verb="helped hide", aid="tucked the treasure under leaves", mutual_phrase="shared the work"),
}

HEROES = [
    ("mouse", "mouse"),
    ("fox", "fox"),
    ("badger", "badger"),
]

TRAITS = ["curious", "careful", "greedy", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a fable about curiosity, a hoard, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--treasure", choices=TREASURES)
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
    out = []
    for p in SETTINGS:
        for h, _ in HEROES:
            for k in HELPERS:
                for t in TREASURES:
                    out.append((p, h, t))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    helper = args.helper or rng.choice(list(HELPERS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    return StoryParams(place=place, hero=hero, helper=helper, treasure=treasure)


def _story_name(hero: str) -> str:
    return {"mouse": "Milo", "fox": "Fenn", "badger": "Bram"}[hero]


def _hero_trait() -> str:
    return "curious"


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_name = _story_name(params.hero)
    hero = world.add(Entity(id=hero_name, kind="character", type=params.hero, label=hero_name))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, label=HELPERS[params.helper].label))
    treasure = TREASURES[params.treasure]

    world.facts.update(hero=hero, helper=helper, treasure=treasure, params=params)

    hero.memes["curiosity"] = 1
    hero.memes["moral_value"] = 0
    helper.memes["mutuality"] = 1

    world.say(f"Once in {world.setting.place}, {hero_name} was a { _hero_trait() } little {params.hero} who loved to peek behind stones and roots.")
    world.say(f"One day, {hero_name} found {treasure.phrase} hidden near {world.setting.place}.")
    world.say(f"{hero_name} felt a strong wish to keep the whole {treasure.label} for itself.")

    world.para()
    world.say(f"But {HELPERS[params.helper].label} had {HELPERS[params.helper].verb} the hoard before, and together they had {HELPERS[params.helper].mutual_phrase}.")
    world.say(f"That made the choice harder, because the treasure was not found by one pair of paws alone.")

    world.para()
    hero.memes["greed"] = 1
    hero.memes["moral_value"] = 0.5
    world.say(f"Then an atrocious wind came rushing through {world.setting.place}.")
    treasure_spill = True
    if treasure_spill:
        world.say(f"The wall cracked, and the hoard spilled into the grass and dust.")
        hero.meters["lost"] = 1
        helper.meters["busy"] = 1

    world.para()
    hero.memes["curiosity"] += 1
    hero.memes["moral_value"] += 1.5
    world.say(f"{hero_name} stopped staring at the empty hiding place and began to gather the pieces back with {helper.label}.")
    world.say(f"At last, {hero_name} chose to share the hoard fairly, and each friend carried away a part.")

    world.para()
    hero.memes["greed"] = 0
    world.say(f"So the little {params.hero} learned that curiosity is good, but moral value is better when a treasure belongs to many helping hearts.")

    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a short fable about a curious {params.hero} who finds a {TREASURES[params.treasure].label} and learns a lesson about sharing.',
            f"Tell a child-friendly moral story set near {params.place} about a hoard, mutual help, and a wise choice.",
            "Write a simple fable where a child character feels curiosity, faces temptation, and ends with a moral lesson.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treasure = f["treasure"]
    params = f["params"]
    hero_name = hero.label
    helper_name = helper.label
    return [
        QAItem(
            question=f"What did {hero_name} find near {params.place}?",
            answer=f"{hero_name} found {treasure.phrase} hidden near {params.place}.",
        ),
        QAItem(
            question=f"Who had helped with the hoard before the storm?",
            answer=f"{helper_name} had helped gather the hoard with {hero_name}.",
        ),
        QAItem(
            question="What lesson did the story end with?",
            answer="It ended with the lesson that curiosity is good, but sharing and moral value matter more than keeping a hoard alone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean in a fable?",
            answer="Curiosity means wanting to know more, explore, and ask questions about something new.",
        ),
        QAItem(
            question="What is a hoard?",
            answer="A hoard is a hidden pile of things saved together in one place.",
        ),
        QAItem(
            question="What does moral value mean?",
            answer="Moral value means the lesson about what is right, fair, and kind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        parts.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(parts)


ASP_RULES = r"""
place(old_wall).
place(orchard).
place(meadow).

hero(mouse).
hero(fox).
hero(badger).

helper(robin).
helper(hedgehog).
helper(rabbit).

treasure(seeds).
treasure(berries).
treasure(coins).

can_story(P,H,T) :- place(P), hero(H), treasure(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h, _ in HEROES:
        lines.append(asp.fact("hero", h))
    for k in HELPERS:
        lines.append(asp.fact("helper", k))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    clingo_set = set(asp.atoms(model, "can_story"))
    py_set = set((p, h, t) for p, h, t in valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_story/3."))
        combos = sorted(set(asp.atoms(model, "can_story")))
        print(f"{len(combos)} compatible combos:")
        for c in combos[:50]:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, h, t in valid_combos()[:5]:
            samples.append(generate(StoryParams(place=p, hero=h, helper="robin", treasure=t, seed=base_seed)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = build_story_params_from_args(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
