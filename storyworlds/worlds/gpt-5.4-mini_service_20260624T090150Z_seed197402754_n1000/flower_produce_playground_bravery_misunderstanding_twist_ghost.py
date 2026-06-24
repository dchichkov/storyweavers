#!/usr/bin/env python3
"""
Ghost Story world: a brave child at the playground thinks a ghost is hiding in
the flowers, but a misunderstanding turns into a gentle twist.

The world is small and classical:
- a child wants to play in a playground
- a strange rustle near flowers and produce sounds spooky
- the child gets scared, then brave
- the mystery resolves with a simple twist: the "ghost" was only a playful
  friend, and the produce basket made the noise

The prose and QA are driven by simulated state, not a fixed template.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the playground"
    affords: set[str] = field(default_factory=lambda: {"play", "explore"})


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    can_rustle: bool = False
    smells: str = ""


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    companion_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.sound: str = ""
        self.mystery_resolved: bool = False
        self.twist_revealed: bool = False

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


# ------------------ registries ------------------

PLACES = {
    "playground": Place(name="the playground", affords={"play", "explore"}),
}

FLOWERS = {
    "daisies": Item(
        id="daisies",
        label="daisies",
        phrase="a patch of white daisies",
        kind="flower",
        can_rustle=True,
        smells="sweet",
    ),
    "tulips": Item(
        id="tulips",
        label="tulips",
        phrase="a row of red tulips",
        kind="flower",
        can_rustle=True,
        smells="fresh",
    ),
}

PRODUCE = {
    "apples": Item(
        id="apples",
        label="apples",
        phrase="a basket of shiny apples",
        kind="produce",
        can_rustle=True,
        smells="sweet",
    ),
    "pears": Item(
        id="pears",
        label="pears",
        phrase="a basket of green pears",
        kind="produce",
        can_rustle=True,
        smells="juicy",
    ),
}

GHOSTY_THINGS = {
    "sheet": "a loose sheet of pale cloth",
    "shadow": "a long shadow from the slide",
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn"]
COMPANION_NAMES = ["Zoe", "Max", "Lily", "Theo", "Ruby", "Noah"]


ASP_RULES = r"""
#show valid/3.
#show twist/4.

valid(Place, Flower, Produce) :- place(Place), flower(Flower), produce(Produce).
twist(Place, Flower, Produce, "true") :- valid(Place, Flower, Produce).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for f in FLOWERS:
        lines.append(asp.fact("flower", f))
        lines.append(asp.fact("rustles", f))
    for pr in PRODUCE:
        lines.append(asp.fact("produce", pr))
        lines.append(asp.fact("rustles", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for flower in FLOWERS:
            for produce in PRODUCE:
                combos.append((place, flower, produce))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story playground world with flowers and produce.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--produce", choices=PRODUCE)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.flower:
        combos = [c for c in combos if c[1] == args.flower]
    if args.produce:
        combos = [c for c in combos if c[2] == args.produce]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, flower, produce = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != name])
    return StoryParams(place=place, child_name=name, child_type="girl" if name in {"Mia", "Nora", "Ava", "Lily", "Ruby"} else "boy", companion_name=companion)


def world_setup(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    friend = world.add(Entity(id=params.companion_name, kind="character", type="girl" if params.companion_name in {"Mia", "Nora", "Ava", "Lily", "Ruby"} else "boy"))
    flower = world.add(Entity(id="flower_patch", kind="thing", type="flower", label=FLOWERS.get("daisies").label, phrase=FLOWERS.get("daisies").phrase))
    produce = world.add(Entity(id="produce_basket", kind="thing", type="produce", label=PRODUCE.get("apples").label, phrase=PRODUCE.get("apples").phrase))
    ghost_clue = world.add(Entity(id="ghost_clue", kind="thing", type="clue", label="a pale cloth", phrase=GHOSTY_THINGS["sheet"]))
    world.facts.update(child=child, friend=friend, flower=flower, produce=produce, ghost_clue=ghost_clue, params=params)
    return world


def propagate(world: World) -> None:
    child: Entity = world.facts["child"]
    if child.memes.get("fear", 0) >= THRESHOLD and "brave" not in world.fired:
        world.fired.add("brave")
        child.memes["bravery"] = child.memes.get("bravery", 0) + 1
        world.say(f"{child.id} took a shaky breath and stood closer to the flowers.")
    if child.memes.get("curious", 0) >= THRESHOLD and "misunderstand" not in world.fired:
        world.fired.add("misunderstand")
        child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0) + 1
    if child.memes.get("bravery", 0) >= THRESHOLD and child.memes.get("misunderstanding", 0) >= THRESHOLD and "twist" not in world.fired:
        world.fired.add("twist")
        world.twist_revealed = True


def tell_story(world: World) -> None:
    child: Entity = world.facts["child"]
    friend: Entity = world.facts["friend"]
    flower: Entity = world.facts["flower"]
    produce: Entity = world.facts["produce"]
    child.memes["curious"] = 1
    world.say(f"At the playground, {child.id} noticed {flower.phrase} by the swings.")
    world.say(f"Beside it sat {produce.phrase}, and the leaves made a tiny rustle in the wind.")
    world.para()
    child.memes["fear"] = 1
    world.say(f"{child.id} froze. The rustle sounded like a ghost hiding in the flowers.")
    world.say(f'"Who is there?" {child.pronoun().capitalize()} whispered, with a brave little wobble in {child.pronoun("possessive")} voice.')
    propagate(world)
    world.para()
    world.say(f"{friend.id} peeked out with a grin and lifted the basket lid.")
    world.say(f"It was not a ghost at all. The basket of {produce.label} had bumped the flower bed, and the cloth from the snack cart had fluttered like a sheet.")
    world.say(f"{child.id} laughed, because the spooky sound had only been a misunderstanding.")
    child.memes["joy"] = 1
    world.para()
    world.say(f"Then {child.id} was brave enough to wave at the flowers instead of running away.")
    world.say(f"{child.id} and {friend.id} shared a {produce.label[:-1]} under the bright sky, and the playground felt friendly again.")
    world.mystery_resolved = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    return [
        f"Write a gentle ghost story set at a playground where {child.id} hears a spooky rustle near flowers and produce.",
        f"Tell a short story for a young child about bravery, misunderstanding, and a twist involving {f['produce'].label}.",
        f"Write a simple playground story where a child thinks a ghost is hiding in the flowers, but the mystery has a kind surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    flower: Entity = f["flower"]
    produce: Entity = f["produce"]
    return [
        QAItem(
            question=f"Where did {child.id} think the ghost might be hiding?",
            answer=f"{child.id} thought the ghost might be hiding near {flower.phrase} at the playground.",
        ),
        QAItem(
            question=f"What made the spooky rustling sound?",
            answer=f"The sound came from the {produce.label} basket and the fluttering cloth, not from a ghost.",
        ),
        QAItem(
            question=f"Who helped solve the misunderstanding?",
            answer=f"{friend.id} helped by showing that the mystery was only a harmless twist, not a real ghost.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt brave and happy after the misunderstanding was solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flower?",
            answer="A flower is a plant part with petals that often smells sweet and can grow in gardens or near play spaces.",
        ),
        QAItem(
            question="What is produce?",
            answer="Produce means fresh fruits and vegetables, like apples or pears, that people can eat.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing because they do not know the full story yet.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you thought was happening.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  mystery_resolved={world.mystery_resolved}")
    lines.append(f"  twist_revealed={world.twist_revealed}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = world_setup(params)
    tell_story(world)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for t in combos:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, combo in enumerate(valid_combos()):
            params = StoryParams(place=combo[0], child_name=CHILD_NAMES[i % len(CHILD_NAMES)], child_type="girl", companion_name=COMPANION_NAMES[i % len(COMPANION_NAMES)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
