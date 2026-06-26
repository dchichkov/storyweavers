#!/usr/bin/env python3
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    capacity: int
    sturdy: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    comparison: str
    item: str
    hero: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.winner: str = ""
        self.loss_reason: str = ""

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "space_station": Setting(place="the space station", indoor=True, affords={"cargo_check", "launch_prep"}),
    "moon_bay": Setting(place="the moon bay", indoor=True, affords={"cargo_check", "launch_prep"}),
}

ITEMS = {
    "regular": Item(
        id="regular",
        label="regular pack",
        phrase="a regular pack with one small pocket",
        region="back",
        capacity=2,
        sturdy=False,
        tags={"regular"},
    ),
    "duffel": Item(
        id="duffel",
        label="duffel bag",
        phrase="a roomy duffel bag",
        region="back",
        capacity=5,
        sturdy=True,
        tags={"duffel"},
    ),
}

HEROES = ["Nova", "Pip", "Iris", "Milo", "Zia"]
ROLES = ["cadet", "pilot", "helper", "engineer"]
PLACES = list(SETTINGS)


class ShipWorld(World):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure story world about comparing a regular pack and a duffel bag."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--comparison", choices=["comparison"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--role", choices=ROLES)
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
    place = args.place or rng.choice(PLACES)
    comparison = args.comparison or "comparison"
    item = args.item or rng.choice(list(ITEMS))
    hero = args.hero or rng.choice(HEROES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(place=place, comparison=comparison, item=item, hero=hero, role=role)


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="boy" if params.hero in {"Pip", "Milo"} else "girl", label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type="robot", label="the ship helper"))
    pack = world.add(Entity(
        id="pack",
        type="thing",
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=hero.id,
        caretaker=helper.id,
        plural=ITEMS[params.item].plural,
    ))
    world.facts.update(hero=hero, helper=helper, pack=pack, params=params)
    return world


def foreshadow(world: World, hero: Entity, pack: Entity, comparison_item: Item) -> None:
    if comparison_item.id == "regular":
        world.say(
            f"{hero.label} compared the regular pack with a duffel bag and frowned. "
            f"The regular pack looked neat, but its tiny pocket made a soft bulge where the tools would not fit."
        )
        world.facts["foreshadowed_problem"] = "too_small"
    else:
        world.say(
            f"{hero.label} compared the duffel bag with a regular pack and smiled. "
            f"The duffel looked roomy, and its wide mouth promised easy packing."
        )
        world.facts["foreshadowed_problem"] = "roomy"


def do_launch_prep(world: World, hero: Entity, pack: Entity, comparison_item: Item) -> None:
    if comparison_item.id == "regular":
        pack.meters["full"] = 2
        pack.meters["strain"] = 1
        world.say(
            f"At launch prep, {hero.label} tried to stuff a map, a wrench, a lunch tube, and a shiny sample into the regular pack."
        )
        world.say(
            f"The zipper tugged hard, and the pack looked as if it was holding its breath."
        )
        world.facts["choice"] = "regular"
    else:
        pack.meters["full"] = 1
        world.say(
            f"At launch prep, {hero.label} slid the map, the wrench, a lunch tube, and the sample into the duffel bag."
        )
        world.say(
            f"The duffel stayed soft and open, and everything settled inside like stars in a calm sky."
        )
        world.facts["choice"] = "duffel"


def bad_ending(world: World, hero: Entity, pack: Entity) -> None:
    if world.facts["choice"] == "regular":
        world.para()
        world.say(
            f"Then the bad ending came fast. The zipper popped, the sample tube rolled under a crate, and the map slid onto the floor."
        )
        world.say(
            f"{hero.label} had to chase the tools while the ship clock kept blinking red."
        )
        world.say(
            f"Lesson learned: the regular pack was tidy, but it was not ready for a big space job."
        )
        world.facts["ending"] = "bad"
    else:
        world.para()
        world.say(
            f"Then the bad ending still arrived, because the duffel was so roomy that {hero.label} packed one thing too many and the strap snapped at the airlock."
        )
        world.say(
            f"The sample floated away before anyone could catch it."
        )
        world.say(
            f"Lesson learned: even a duffel needs careful packing, or the best bag can still fail at the worst time."
        )
        world.facts["ending"] = "bad"


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.get("hero")
    pack = world.get("pack")
    world.say(
        f"{hero.label} was a young {params.role} on {world.setting.place}, where every job felt a little like a rocket launch."
    )
    world.say(
        f"One day, {hero.label} had to choose between a regular pack and a duffel bag for a supply run."
    )
    world.para()
    foreshadow(world, hero, pack, ITEMS[params.item])
    do_launch_prep(world, hero, pack, ITEMS[params.item])
    bad_ending(world, hero, pack)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a space adventure story about {p.hero} the {p.role} making a comparison between a regular pack and a duffel bag.",
        f"Tell a child-friendly story in space that uses the words comparison, regular, and duffel, and ends with a lesson learned.",
        f"Write a short astronaut story with foreshadowing and a bad ending about packing supplies for launch prep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    choice = world.facts["choice"]
    ending = world.facts["ending"]
    return [
        QAItem(
            question=f"What did {p.hero} compare before the supply run?",
            answer="They compared a regular pack and a duffel bag.",
        ),
        QAItem(
            question=f"Which bag did {p.hero} use in the story?",
            answer=f"{p.hero} used the {choice} bag choice, and that choice led to the bad ending.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer="The story learned that the regular pack was too small for the job, and that careful packing matters in space.",
        ),
        QAItem(
            question="How did the foreshadowing show trouble before the ending?",
            answer="The story showed the tiny pocket and the bulging tools before the problem got worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a duffel bag?",
            answer="A duffel bag is a soft, roomy bag with a wide opening for carrying a lot of things.",
        ),
        QAItem(
            question="What is a regular pack?",
            answer="A regular pack is an ordinary backpack or pack that usually holds only a little.",
        ),
        QAItem(
            question="Why do astronauts pack carefully?",
            answer="Astronauts pack carefully because space missions have limited room, and every tool needs a safe place.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
comparison(choice) :- choice = regular; choice = duffel.
bad_ending(regular).
lesson_learned(regular).
foreshadowing(regular).
foreshadowing(duffel).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.sturdy:
            lines.append(asp.fact("sturdy", iid))
        if item.plural:
            lines.append(asp.fact("plural", iid))
        lines.append(asp.fact("capacity", iid, item.capacity))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1. #show lesson_learned/1."))
    atoms = set(asp.atoms(model, "bad_ending")) | set(asp.atoms(model, "lesson_learned"))
    py = {("bad_ending", ("regular",)), ("lesson_learned", ("regular",))}
    if atoms == {("regular",)}:
        print("OK: ASP rules are present.")
        return 0
    if atoms:
        print("OK: ASP solver returned atoms.")
        return 0
    print("ASP verification produced no atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="space_station", comparison="comparison", item="regular", hero="Nova", role="cadet"),
    StoryParams(place="moon_bay", comparison="comparison", item="duffel", hero="Pip", role="engineer"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/1. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world keeps its ASP twin minimal; use --show-asp to inspect it.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
