#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/impound_minus_foreshadowing_ghost_story.py
===============================================================================================================

A small ghost-story world with a foreshadowed turn: a child visits an impound
lot at dusk, notices a missing thing, and learns that the quiet clues were
leading toward a kind ending all along.

Premise:
- A child and a grown-up go to an impound yard to rescue a small possession.
- The place feels spooky, but the story stays gentle and child-facing.

Turn:
- Foreshadowing clues show that a ghost is not there to frighten anyone.
- The missing piece is "minus" something important, and that absence matters.

Resolution:
- The ghost helps reveal where the missing thing went.
- The child leaves the impound lot with relief, and the ghost is no longer lonely.

This world uses meters for physical state and memes for emotional state.
"""

from __future__ import annotations

import argparse
import copy
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    eerie: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    type: str
    missing_part: str
    owner_roles: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class GhostSpec:
    id: str
    label: str
    clue: str
    help_text: str
    reveal_text: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


def meters_nonzero(ent: Entity) -> dict[str, float]:
    return {k: v for k, v in ent.meters.items() if v}


def memes_nonzero(ent: Entity) -> dict[str, float]:
    return {k: v for k, v in ent.memes.items() if v}


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place={world.place.name} eerie={world.place.eerie}")
    for e in world.entities.values():
        bits = []
        m = meters_nonzero(e)
        s = memes_nonzero(e)
        if m:
            bits.append(f"meters={m}")
        if s:
            bits.append(f"memes={s}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def story_intro(world: World, child: Entity, grownup: Entity, obj: Entity) -> None:
    world.say(
        f"{child.id} and {grownup.id} came to the impound lot at dusk because {obj.phrase} had gone missing."
    )
    world.say(
        f"The yard was lined with tow trucks, chain-link shadows, and one tall gate that squeaked in the wind."
    )
    if world.place.eerie:
        world.say(
            f"It felt spooky, but not mean, like the kind of spooky that whispers before it tells the truth."
        )


def foreshadow(world: World, child: Entity, ghost: Entity, obj: Entity) -> None:
    child.memes["curious"] = child.memes.get("curious", 0) + 1
    child.memes["wary"] = child.memes.get("wary", 0) + 0.5
    world.say(
        f"Then {child.id} noticed a pale little glow by the fence."
    )
    world.say(
        f"It blinked once, and a cold breeze tugged at {child.pronoun('possessive')} sleeve like a quiet hint."
    )
    world.say(
        f"The glow left tiny clues: a soft tap-tap on a chain, a missing sparkle, and the feeling that something was minus one important piece."
    )
    world.say(
        f"That was the first foreshadowing, though {child.id} did not know it yet."
    )


def worry(world: World, child: Entity, grownup: Entity, obj: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    world.say(
        f"{child.id} hugged {obj.it()} close and asked if the night was going to stay strange."
    )
    world.say(
        f"{grownup.id} said the strange kind of quiet often meant someone was trying to show the way home."
    )


def reveal(world: World, ghost: Entity, obj: Entity) -> None:
    ghost.memes["lonely"] = ghost.memes.get("lonely", 0) + 1
    ghost.memes["hope"] = ghost.memes.get("hope", 0) + 1
    world.say(
        f"The little glow drifted nearer and became a friendly ghost with round eyes and a shy smile."
    )
    world.say(
        f"It was the ghost of the lost helper from the lot, and it was not there to scare anybody."
    )
    world.say(
        f"It pointed to a heap of tarp and said, softly, that {obj.label} had been left there when the truck came."
    )


def fix_missing(world: World, child: Entity, grownup: Entity, obj: Entity, ghost: Entity) -> None:
    obj.meters["found"] = 1
    child.memes["joy"] = child.memes.get("joy", 0) + 2
    child.memes["fear"] = 0
    ghost.memes["lonely"] = 0
    ghost.memes["warm"] = ghost.memes.get("warm", 0) + 1
    world.say(
        f"{child.id} and {grownup.id} lifted the tarp, and there it was: {obj.phrase}, safe and a little dusty."
    )
    world.say(
        f"The ghost smiled wider, because the missing part was no longer missing."
    )
    world.say(
        f"{child.id} said thank you, and the ghost looked less like a mystery and more like a friend."
    )
    world.say(
        f"When they drove away from the impound lot, the fence did not seem spooky anymore; it just looked like a place where clues had waited patiently."
    )


def tell(world: World, child: Entity, grownup: Entity, obj: Entity, ghost: Entity) -> World:
    story_intro(world, child, grownup, obj)
    world.para()
    foreshadow(world, child, ghost, obj)
    worry(world, child, grownup, obj)
    world.para()
    reveal(world, ghost, obj)
    fix_missing(world, child, grownup, obj, ghost)
    world.facts.update(child=child, grownup=grownup, obj=obj, ghost=ghost)
    return world


IMPound_PLACES = {
    "lot": Place(name="the impound lot", eerie=True, afford={"search", "find"}),
    "yard": Place(name="the tow yard", eerie=True, afford={"search", "find"}),
}

OBJECTS = {
    "bike": ObjectSpec(
        id="bike",
        label="bike",
        phrase="a red bike with a silver bell",
        type="bike",
        missing_part="bell",
        owner_roles={"girl", "boy"},
    ),
    "skateboard": ObjectSpec(
        id="skateboard",
        label="skateboard",
        phrase="a blue skateboard with sticker stars",
        type="skateboard",
        missing_part="wheel",
        owner_roles={"girl", "boy"},
    ),
    "backpack": ObjectSpec(
        id="backpack",
        label="backpack",
        phrase="a green backpack with a cat patch",
        type="backpack",
        missing_part="zipper",
        owner_roles={"girl", "boy"},
    ),
}

GHOSTS = {
    "bellghost": GhostSpec(
        id="bellghost",
        label="the bell ghost",
        clue="a tiny ring in the dark",
        help_text="It had followed the sound of the missing bell.",
        reveal_text="The bell had fallen into the tarp pile.",
    ),
    "wheelghost": GhostSpec(
        id="wheelghost",
        label="the wheel ghost",
        clue="a rolling whisper by the fence",
        help_text="It had watched the loose wheel roll under cover.",
        reveal_text="The wheel had spun into the shadow behind the tow truck.",
    ),
    "zipperghost": GhostSpec(
        id="zipperghost",
        label="the zipper ghost",
        clue="a silver glimmer by the crate",
        help_text="It had noticed the zipper snagged on twine.",
        reveal_text="The zipper was caught under the crate, waiting to be found.",
    ),
}

CHILD_NAMES = ["Mina", "Eli", "Tessa", "Noah", "Lena", "Owen", "Nia", "Jude"]
GROWNUP_NAMES = ["Mom", "Dad", "Aunt Rae", "Uncle Ben", "Grandma"]
GHOST_NAMES = ["Pip", "Murmur", "Lantern", "Whisper"]


@dataclass
class StoryParams:
    place: str
    obj: str
    ghost: str
    child_name: str
    child_gender: str
    grownup: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle foreshadowed ghost story in an impound lot.")
    ap.add_argument("--place", choices=IMPound_PLACES)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["Mom", "Dad", "Aunt Rae", "Uncle Ben", "Grandma"])
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
    combos = []
    for place in IMPound_PLACES:
        for obj in OBJECTS:
            for ghost in GHOSTS:
                combos.append((place, obj, ghost))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.obj:
        combos = [c for c in combos if c[1] == args.obj]
    if args.ghost:
        combos = [c for c in combos if c[2] == args.ghost]
    if not combos:
        raise StoryError("No valid impound-ghost combination matches those options.")
    place, obj, ghost = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    return StoryParams(place=place, obj=obj, ghost=ghost, child_name=name, child_gender=gender, grownup=grownup)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    obj = f["obj"]
    ghost = f["ghost"]
    return [
        QAItem(
            question=f"Why did {child.id} feel uneasy at the impound lot?",
            answer=(
                f"{child.id} felt uneasy because the impound lot was dark and full of chain-link shadows, "
                f"and {obj.phrase} was still missing. The spooky quiet made the missing thing feel even bigger."
            ),
        ),
        QAItem(
            question=f"What was the foreshadowing clue before the ghost spoke?",
            answer=(
                f"The foreshadowing clue was a pale glow, a soft tap on a chain, and a cold breeze that felt like a hint. "
                f"It showed that something important was waiting to be found."
            ),
        ),
        QAItem(
            question=f"How did the ghost help in the end?",
            answer=(
                f"{ghost.label} led {child.id} and {grownup.id} to the hidden place where {obj.label} had been left. "
                f"That helped them recover the missing part and turned the scary night into a kind one."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an impound lot?",
            answer="An impound lot is a place where towed vehicles or lost things may be kept until someone comes to get them back.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives little clues early so the reader can guess that something important will happen later.",
        ),
        QAItem(
            question="What does minus mean when something is minus a part?",
            answer="When something is minus a part, it is missing that part or has one less piece than it should.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly ghost story set at {world.place.name} that uses foreshadowing and the word 'impound'.",
        f"Tell a gentle spooky story where {f['child'].id} discovers that {f['obj'].label} is minus one important part.",
        "Create a short story in which a ghost leaves clues before helping a child find a lost object.",
    ]


def generate(params: StoryParams) -> StorySample:
    place = IMPound_PLACES[params.place]
    objspec = OBJECTS[params.obj]
    ghostspec = GHOSTS[params.ghost]
    world = World(place)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
    ))
    grownup = world.add(Entity(
        id=params.grownup,
        kind="character",
        type="mother" if params.grownup in {"Mom", "Grandma", "Aunt Rae"} else "father",
        label=params.grownup,
    ))
    obj = world.add(Entity(
        id=objspec.id,
        type=objspec.type,
        label=objspec.label,
        phrase=objspec.phrase,
        owner=child.id,
        caretaker=grownup.id,
    ))
    ghost = world.add(Entity(
        id=ghostspec.id,
        kind="character",
        type="ghost",
        label=ghostspec.label,
    ))
    tell(world, child, grownup, obj, ghost)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
place(lot).
place(yard).

obj(bike).
obj(skateboard).
obj(backpack).

ghost(bellghost).
ghost(wheelghost).
ghost(zipperghost).

valid_story(P,O,G) :- place(P), obj(O), ghost(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in IMPound_PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("obj", o))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


CURATED = [
    StoryParams(place="lot", obj="bike", ghost="bellghost", child_name="Mina", child_gender="girl", grownup="Mom"),
    StoryParams(place="yard", obj="skateboard", ghost="wheelghost", child_name="Owen", child_gender="boy", grownup="Dad"),
    StoryParams(place="lot", obj="backpack", ghost="zipperghost", child_name="Lena", child_gender="girl", grownup="Grandma"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.child_name}: {p.obj} at {p.place} with {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
