#!/usr/bin/env python3
"""
storyworlds/worlds/hill_boomsie_native_bravery_mystery.py
==========================================================

A small mystery storyworld about a brave child, a quiet hill, and a native
boomsie whose lost trail must be found.

The seed image:
- A child climbs a hill and notices odd boomsie signs.
- Someone native to the place knows the trail, but the clue is hidden.
- Bravery means going up the hill, asking careful questions, and not turning
  back when the wind or shadows make the path feel strange.

The simulation keeps two kinds of state:
- physical meters: height climbed, trail clues found, lantern light, footprints
- emotional memes: curiosity, worry, bravery, relief, trust

The story is built from a short causal chain:
setup -> odd clue on the hill -> brave search -> solved mystery -> calm ending.
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
    native: bool = False
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case] if self.type == "girl" else {"subject": "he", "object": "him", "possessive": "his"}[case] if self.type == "boy" else {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill"
    has_path: bool = True
    has_cave: bool = False
    has_windbreak: bool = True


@dataclass
class Clue:
    kind: str
    text: str
    weight: float = 1.0


@dataclass
class StoryParams:
    name: str
    gender: str
    guide: str
    clue_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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

    def clone(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


def _say_better(world: World, text: str) -> None:
    world.say(text)


def place_line(world: World) -> str:
    return f"The hill rose up behind the tall grass, with a narrow path curling to the top."


def introduce(world: World, child: Entity) -> None:
    _say_better(world, f"{child.id} was a little brave {child.type} who liked quiet mysteries.")
    _say_better(world, f"{child.id} lived near {world.setting.place} and noticed tiny things that others missed.")


def boomsie_line(world: World, boomsie: Entity) -> None:
    _say_better(world, f"People said {boomsie.label} was native to the hill country, and it knew every bush and stone.")
    _say_better(world, f"It was small, quick, and shy, with a habit of hiding when the wind moved the grass.")


def clue_line(world: World, clue: Clue) -> None:
    if clue.kind == "print":
        _say_better(world, "One morning, tiny prints appeared in the dust near the hill path.")
    elif clue.kind == "ribbon":
        _say_better(world, "A faded ribbon snagged on a thorn, fluttering like it had been left in a hurry.")
    elif clue.kind == "bell":
        _say_better(world, "A small silver bell was found half-buried beside a flat stone.")
    else:
        _say_better(world, clue.text)


def start_mystery(world: World, child: Entity, clue: Clue) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 0.2
    _say_better(world, f"{child.id} knelt down to look more closely, because the clue did not belong there.")
    _say_better(world, f"{child.pronoun().capitalize()} wondered who had passed by {world.setting.place} so early.")


def climb(world: World, child: Entity) -> None:
    child.meters["height"] = child.meters.get("height", 0) + 1
    child.memes["bravery"] = child.memes.get("bravery", 0) + 1
    _say_better(world, f"{child.id} took a breath and started up the hill instead of turning away.")
    _say_better(world, f"The path felt steep, but {child.id} kept going one careful step at a time.")


def seek(world: World, child: Entity, boomsie: Entity, clue: Clue) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 0.5
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    _say_better(world, f"Near a windbreak of low trees, {child.id} found more signs: {clue.text.lower()}.")
    _say_better(world, f"That meant the mystery was still nearby, and {child.id} had been right to keep looking.")
    if boomsie.native:
        _say_better(world, f"At last, {child.id} heard a soft rustle and saw {boomsie.label} watching from behind a rock.")
    else:
        _say_better(world, f"At last, {child.id} saw a shy little boomsie watching from behind a rock.")


def reveal(world: World, child: Entity, boomsie: Entity, clue: Clue) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0) + 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.facts["solved"] = True
    world.facts["clue_kind"] = clue.kind
    _say_better(world, f"{child.id} did not shout. {child.pronoun().capitalize()} spoke softly, so the shy boomsie would not run.")
    _say_better(world, f"It turned out the boomsie had dropped the clue while carrying a little nest bundle up the hill.")
    _say_better(world, f"The bundle had snagged, and the boomsie had come back looking for it all morning.")


def end(world: World, child: Entity, boomsie: Entity) -> None:
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    child.memes["worry"] = 0
    _say_better(world, f"{child.id} led the boomsie back to the snagged place and helped free the lost bundle.")
    _say_better(world, f"Then {child.id} smiled as the boomsie tucked it close and darted home across the hill.")
    _say_better(world, f"By sunset, the hill was quiet again, and {child.id} felt proud for being brave enough to solve the mystery.")


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    guide = world.add(Entity(id="guide", kind="character", type="elder", label=params.guide, native=True))
    boomsie = world.add(Entity(id="boomsie", kind="character", type="boomsie", label="the boomsie", native=True))
    clue = Clue(
        kind=params.clue_kind,
        text={
            "print": "Tiny prints led in a half-circle around the hill stone",
            "ribbon": "A faded ribbon brushed the thorny brush",
            "bell": "A silver bell chimed once from the grass",
        }[params.clue_kind],
    )

    world.facts.update(child=child, guide=guide, boomsie=boomsie, clue=clue, setting=world.setting)

    introduce(world, child)
    boomsie_line(world, boomsie)
    world.say(place_line(world))
    world.para()
    clue_line(world, clue)
    start_mystery(world, child, clue)
    climb(world, child)
    world.say(f"{guide.label} said the hill was safe, but only if {child.id} stayed on the path and listened closely.")
    seek(world, child, boomsie, clue)
    world.para()
    reveal(world, child, boomsie, clue)
    end(world, child, boomsie)
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    clue: Clue = world.facts["clue"]
    return [
        'Write a short mystery story for a young child about a brave kid on a hill.',
        f"Tell a gentle mystery where {c.id} finds {clue.kind}-type clues and meets a native boomsie.",
        f"Write a simple story using the words hill, boomsie, and native, and let bravery solve the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c: Entity = world.facts["child"]
    b: Entity = world.facts["boomsie"]
    clue: Clue = world.facts["clue"]
    return [
        QAItem(
            question=f"Who climbed the hill to solve the mystery?",
            answer=f"{c.id} did. {c.pronoun().capitalize()} was the brave child who kept following the clues up the hill.",
        ),
        QAItem(
            question=f"What was mysterious about the clue on the hill?",
            answer=f"The {clue.kind} clue did not belong there, so it made {c.id} wonder who had left it and why.",
        ),
        QAItem(
            question=f"Why did the boomsie matter in the story?",
            answer=f"The boomsie was native to the hill and knew the place well, so it could explain where the clue had come from.",
        ),
        QAItem(
            question=f"How did bravery help {c.id}?",
            answer=f"Bravery helped {c.id} keep walking, ask careful questions, and stay calm until the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hill?",
            answer="A hill is a raised piece of land that slopes upward, so you can walk or climb to a higher place.",
        ),
        QAItem(
            question="What does native mean?",
            answer="Native means something belongs naturally to a place or has lived there for a very long time.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being able to do a hard or scary thing while staying calm and doing what is right.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.native:
            bits.append("native=True")
        lines.append(f"{e.id}: ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {"hill": Setting(place="the hill")}
CLUES = {"print": Clue("print", ""), "ribbon": Clue("ribbon", ""), "bell": Clue("bell", "")}
NAMES = {"girl": ["Mina", "Lina", "Rosa", "Nia"], "boy": ["Tomas", "Eli", "Noel", "Bren"]}


@dataclass
class ASPChoice:
    kind: str
    clue: str


ASP_RULES = r"""
% A valid mystery is one where bravery, hill, native guide, and clue all appear.
valid_story(H, G, C) :- hero(H), guide(G), clue(C), brave(H), native(G), hill(Hill), solved(H, C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hill", "hill"),
        asp.fact("native", "boomsie"),
        asp.fact("hero", "child"),
        asp.fact("guide", "guide"),
        asp.fact("brave", "child"),
        asp.fact("solved", "child", "print"),
        asp.fact("clue", "print"),
        asp.fact("clue", "ribbon"),
        asp.fact("clue", "bell"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("child", "guide", c) for c in CLUES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bravery-and-mystery storyworld on a hill.")
    ap.add_argument("--name", choices=sum(NAMES.values(), []))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", default=None)
    ap.add_argument("--clue-kind", choices=list(CLUES))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    clue_kind = args.clue_kind or rng.choice(list(CLUES))
    guide = args.guide or rng.choice(["Old Mara", "Uncle Fen", "Aunt Suri"])
    return StoryParams(name=name, gender=gender, guide=guide, clue_kind=clue_kind)


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
    StoryParams(name="Mina", gender="girl", guide="Old Mara", clue_kind="print"),
    StoryParams(name="Tomas", gender="boy", guide="Uncle Fen", clue_kind="ribbon"),
    StoryParams(name="Rosa", gender="girl", guide="Aunt Suri", clue_kind="bell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid story patterns:")
        for t in vals:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
