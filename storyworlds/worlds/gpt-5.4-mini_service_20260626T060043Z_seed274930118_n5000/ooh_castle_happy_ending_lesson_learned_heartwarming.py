#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ooh_castle_happy_ending_lesson_learned_heartwarming.py
=============================================================================================================

A tiny heartwarming story world about a child in a castle who learns a gentle
lesson and ends with a happy ending.

Seed image:
- "ooh"
- "castle"

Premise:
A child visits a castle full of echoes and shiny things, gets excited, and
learns that the kindest way to enjoy a grand place is to slow down and be
gentle with a shy little creature who lives there.

The world uses meters and memes:
- meters track loudness, calm, and comfort in the physical scene
- memes track excitement, patience, trust, and pride in the social/emotional scene

The story is kept short, concrete, and state-driven:
beginning -> excitement in the castle
middle -> a warning and a tense choice
turn -> a gentle compromise
ending -> the child learns a lesson and the shy creature feels safe
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

CASTLE_ROOMS = ("courtyard", "great_hall", "tower_stairs", "sunny_window")


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Castle:
    place: str = "the castle"
    rooms: tuple[str, ...] = CASTLE_ROOMS
    echo_factor: float = 1.0


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    room: str
    seed: Optional[int] = None


class World:
    def __init__(self, castle: Castle) -> None:
        self.castle = castle
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def bump_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + amount


def bump_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = meme(ent, key) + amount


def quiet_down(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    kitten = world.get("kitten")
    if meter(child, "loud") >= 1.0 and kitten.location == child.location:
        if ("fright", "kitten") not in world.fired:
            world.fired.add(("fright", "kitten"))
            bump_meme(kitten, "fear", 1.0)
            out.append("The little kitten flattened its ears at all that noise.")
    if meter(child, "calm") >= 1.0:
        if ("soothe", "kitten") not in world.fired:
            world.fired.add(("soothe", "kitten"))
            bump_meme(kitten, "trust", 1.0)
            bump_meter(kitten, "comfort", 1.0)
            out.append("The quiet made the kitten feel safer.")
    return out


def lesson_settles(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    kitten = world.get("kitten")
    if meme(kitten, "trust") >= 1.0 and ("lesson", "child") not in world.fired:
        world.fired.add(("lesson", "child"))
        bump_meme(child, "pride", 1.0)
        bump_meme(child, "wisdom", 1.0)
        out.append("The child learned that gentle hands could be braver than noisy ones.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (quiet_down, lesson_settles):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _actor(hero: Entity) -> str:
    return f"{hero.id}"


def tell(params: StoryParams) -> World:
    world = World(Castle(place="the castle"))
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=params.gender,
            traits=["little", params.trait],
            meters={"loud": 0.0, "calm": 0.0},
            memes={"excitement": 1.0, "patience": 0.0, "pride": 0.0, "wisdom": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=params.parent,
            label=f"the {params.parent}",
            traits=["gentle"],
            meters={"calm": 0.0},
            memes={"care": 1.0},
        )
    )
    kitten = world.add(
        Entity(
            id="kitten",
            kind="character",
            type="thing",
            label="kitten",
            phrase="a shy little kitten",
            traits=["shy"],
            location=params.room,
            meters={"comfort": 0.0},
            memes={"fear": 0.0, "trust": 0.0},
        )
    )

    world.say(
        f"Ooh, the castle was huge and shiny, and {child.id} stepped in with wide eyes."
    )
    world.say(
        f"{child.id} was a little {params.trait} {params.gender} who loved grand places and echoing floors."
    )
    world.say(
        f"{child.id} wanted to explore {params.room.replace('_', ' ')} right away, because every stone looked like a new surprise."
    )

    world.para()
    world.say(
        f"Inside the castle, {child.id} spotted a shy kitten curled near {params.room.replace('_', ' ')}."
    )
    bump_meter(child, "loud", 1.0)
    bump_meme(child, "excitement", 1.0)
    world.say(
        f"{child.id} gasped, but that made the room ring out louder than a drum."
    )
    if params.room in {"tower_stairs", "sunny_window"}:
        world.say(
            f"The {params.room.replace('_', ' ')} felt tricky for little paws and little feet."
        )
    bump_meme(parent, "worry", 1.0)
    world.say(
        f'The {params.parent} held up a hand and said, "Slow down. The kitten needs a soft hello, not a big shout."'
    )

    world.para()
    bump_meme(child, "patience", 1.0)
    bump_meter(child, "loud", -1.0)
    bump_meter(child, "calm", 1.0)
    world.say(
        f"{child.id} took a breath, crouched low, and tried again with a whisper."
    )
    world.say(
        f"{child.id} padded closer, then tucked a warm cloth beside the kitten like a tiny blanket."
    )
    kitten.location = params.room
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"The kitten blinked, stepped onto the cloth, and began to purr."
    )
    world.say(
        f"{child.id} smiled because the castle was still exciting, only now it felt kinder too."
    )
    world.say(
        f"In the end, {child.id} learned that a gentle voice could make a big castle feel safe."
    )

    world.facts.update(
        child=child,
        parent=parent,
        kitten=kitten,
        params=params,
    )
    return world


SETTINGS = {
    "castle": Castle(place="the castle"),
}

ROOMS = {
    "courtyard": "courtyard",
    "great_hall": "great hall",
    "tower_stairs": "tower stairs",
    "sunny_window": "sunny window",
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Theo", "Max", "Ben"],
}
TRAITS = ["curious", "cheerful", "brave", "gentle", "spirited"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming castle story world with a lesson learned."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("castle", room) for room in ROOMS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES[gender])
    if room not in ROOMS:
        raise StoryError("The castle story only works in one of the castle rooms.")
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, room=room)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    child = world.facts["child"]
    return [
        'Write a short heartwarming story about a child in a castle who says "ooh" and learns a gentle lesson.',
        f"Tell a story where {child.id} explores a castle room, gets too excited, and then discovers a kinder way to act.",
        f"Write a simple castle story where a {p.gender} named {p.name} learns that being gentle can help a shy kitten feel safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    kitten = world.facts["kitten"]
    room = p.room.replace("_", " ")
    return [
        QAItem(
            question=f"Who was the castle story about?",
            answer=f"It was about {child.id}, a little {p.trait} {p.gender}, and the {p.parent} who helped keep the castle calm.",
        ),
        QAItem(
            question=f"What did {child.id} learn in the castle?",
            answer=f"{child.id} learned that a gentle voice and soft hands can make a shy kitten feel safe.",
        ),
        QAItem(
            question=f"Why did the {p.parent} ask {child.id} to slow down?",
            answer=f"The {p.parent} wanted {child.id} to be gentle because the kitten was shy and the room was echoey inside the {room}.",
        ),
        QAItem(
            question=f"What happened after {child.id} used a whisper instead of a shout?",
            answer=f"The kitten relaxed, stepped onto the warm cloth, and began to purr near {room}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {child.id} felt proud, the kitten felt safe, and the castle felt warm and kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a castle?",
            answer="A castle is a very big old building with strong walls, rooms, and tall places to explore.",
        ),
        QAItem(
            question="Why do quiet voices matter in echoey places?",
            answer="Quiet voices matter because sounds bounce around in echoey places, so a whisper is easier for everyone to hear kindly.",
        ),
        QAItem(
            question="What does a shy kitten need?",
            answer="A shy kitten usually needs soft words, gentle hands, and a safe spot where it can relax.",
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
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items())}}}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:7} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", trait="curious", room="courtyard"),
    StoryParams(name="Leo", gender="boy", parent="father", trait="gentle", room="great_hall"),
    StoryParams(name="Nora", gender="girl", parent="mother", trait="brave", room="sunny_window"),
    StoryParams(name="Finn", gender="boy", parent="father", trait="cheerful", room="tower_stairs"),
]


ASP_RULES = r"""
room_valid(courtyard).
room_valid(great_hall).
room_valid(tower_stairs).
room_valid(sunny_window).

story_valid(Room) :- room_valid(Room).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("room", r) for r in ROOMS)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/1."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((room,) for _, room in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} rooms).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_valid/1."))
        vals = sorted(set(asp.atoms(model, "story_valid")))
        print(f"{len(vals)} valid castle-room choices:")
        for (room,) in vals:
            print(f"  {room}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.room} in the castle"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
