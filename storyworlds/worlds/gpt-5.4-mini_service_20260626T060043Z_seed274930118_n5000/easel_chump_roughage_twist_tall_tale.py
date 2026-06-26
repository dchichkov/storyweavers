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


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    object: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


PLACES = {
    "barn": "the big red barn",
    "yard": "the windy yard",
    "porch": "the crooked porch",
}

HEROES = [
    ("Jeb", "boy"),
    ("Mabel", "girl"),
    ("Hank", "boy"),
    ("Rose", "girl"),
]

SIDEKICKS = [
    ("Old Twist", "man"),
    ("Aunt Twist", "woman"),
]

OBJECTS = {
    "easel": {
        "label": "easel",
        "phrase": "a tall easel with a wobbley leg",
        "risk": "paint",
        "mess": "spattered",
        "end": "stood steady at last",
    },
    "roughage": {
        "label": "roughage",
        "phrase": "a wagonload of roughage for the goat",
        "risk": "hay",
        "mess": "rustled",
        "end": "stayed piled neat and high",
    },
}

ASP_RULES = r"""
object(object_id) :- object_fact(object_id).
character(character_id) :- character_fact(character_id).
at_risk(O) :- object_fact(O), risky(O).
fixable(O) :- at_risk(O), helper(H), twist(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for oid in OBJECTS:
        lines.append(asp.fact("object_fact", oid))
    for name, _type in HEROES + SIDEKICKS:
        lines.append(asp.fact("character_fact", name))
    lines.append(asp.fact("helper", "Twist"))
    lines.append(asp.fact("twist", "Twist"))
    lines.append(asp.fact("risky", "easel"))
    lines.append(asp.fact("risky", "roughage"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: an easel, roughage, and Twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--object", choices=OBJECTS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("barn", "easel"), ("yard", "roughage"), ("porch", "easel"), ("porch", "roughage")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if not combos:
        raise StoryError("No reasonable tall tale fits those options.")
    place, obj = rng.choice(combos)
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    sidekick = args.sidekick or "Twist"
    if args.sidekick and args.sidekick != "Twist":
        raise StoryError("This world only uses Twist as the helper.")
    return StoryParams(place=place, hero=hero, sidekick=sidekick, object=obj)


def generate_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero_type = dict(HEROES).get(params.hero, "boy")
    hero = world.add(Entity(id=params.hero, kind="character", type=hero_type))
    twist = world.add(Entity(id="Twist", kind="character", type="man"))
    obj_cfg = OBJECTS[params.object]
    obj = world.add(Entity(id=params.object, label=obj_cfg["label"], type=obj_cfg["label"], owner=hero.id))
    world.facts.update(hero=hero, twist=twist, obj=obj, params=params)

    if params.object == "easel":
        world.say(f"{hero.id} was a tall tale chump who loved a grand old easel.")
        world.say(f"At {world.place}, {hero.id} wanted to paint a sky-blue horse on the {obj.label}.")
        world.para()
        world.say(f"That day the wind came waltzing through the boards, and the {obj.label} started to wobble.")
        world.say(f"{hero.id} tried to hold it with one hand and the paint with the other, but that was a chump's trick.")
        world.say(f"Then {twist.id} came along with a clever twist of rope and said, \"Let's tie the leg to the post.\"")
        world.para()
        world.say(f"{hero.id} gave the rope one great turn, and the {obj.label} {obj_cfg['end']}.")
        world.say(f"In the end, the painting looked bold as thunder, and the barn stayed neat as a whistle.")
    else:
        world.say(f"{hero.id} was a lanky chump who had one job: haul the roughage to the goat.")
        world.say(f"At {world.place}, the roughage was piled high as a hay mountain, and everyone said it would roll away.")
        world.para()
        world.say(f"{hero.id} tried to lug the wagon alone, but the load slid and the path got slick with straw.")
        world.say(f"Then {twist.id} made a quick twist with the harness and showed {hero.id} how to wedge the wheels.")
        world.para()
        world.say(f"Together they gave the wagon one mighty shove, and the roughage {obj_cfg['end']}.")
        world.say(f"The goat got fed, the yard stayed tidy, and even the foolish chump stood a little taller.")

    return world


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    if p.object == "easel":
        return [
            QAItem(
                question=f"What did {p.hero} want to do with the easel?",
                answer=f"{p.hero} wanted to paint a sky-blue horse on the easel.",
            ),
            QAItem(
                question="Who helped make the easel steady?",
                answer="Twist helped by tying the leg to the post with a clever twist of rope.",
            ),
            QAItem(
                question=f"What changed by the end of the story at {world.place}?",
                answer="The easel stood steady at last, and the painting could be finished safely.",
            ),
        ]
    return [
        QAItem(
            question=f"What was {p.hero} supposed to do with the roughage?",
            answer=f"{p.hero} was supposed to haul the roughage to the goat.",
        ),
        QAItem(
            question="What did Twist do to help the wagon?",
            answer="Twist made a quick twist with the harness and showed how to wedge the wheels.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The roughage stayed piled neat and high, and the goat got fed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an easel for?",
            answer="An easel is a stand that holds something up while you paint or draw.",
        ),
        QAItem(
            question="What is roughage?",
            answer="Roughage is coarse plant food, like hay or straw, that animals can eat.",
        ),
        QAItem(
            question="What does the word twist mean here?",
            answer="A twist is a turning or turning motion, like winding rope or turning a clever plan.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a tall tale about {p.hero}, an easel, and a windy problem at {world.place}.",
        f"Tell a child-friendly story where Twist helps a chump solve trouble with {p.object}.",
        "Make the story feel like a tall tale, with a big problem, a clever twist, and a happy ending.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", hero="Jeb", sidekick="Twist", object="easel"),
    StoryParams(place="yard", hero="Mabel", sidekick="Twist", object="roughage"),
]


def asp_verify() -> int:
    import asp
    program = asp_program("#show fixable/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "fixable"))
    py = {("easel",), ("roughage",)}
    if atoms == py:
        print(f"OK: clingo gate matches Python ({len(py)} fixes).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo:", sorted(atoms))
    print("python:", sorted(py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fixable/1."))
    return sorted(set(asp.atoms(model, "fixable")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show fixable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} fixable objects:")
        for (name,) in vals:
            print(f"  {name}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
            header = f"### {p.hero} with {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
