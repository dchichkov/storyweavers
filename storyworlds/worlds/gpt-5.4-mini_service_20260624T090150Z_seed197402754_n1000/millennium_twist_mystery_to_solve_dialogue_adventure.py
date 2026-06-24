#!/usr/bin/env python3
"""
A small storyworld about a millennium celebration, a mystery to solve, and a
twist that turns into a friendly adventure through dialogue.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    detail: str
    hidden: str


@dataclass
class Mystery:
    id: str
    clue: str
    mistaken_guess: str
    twist: str
    solved_by: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
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


PLACES = {
    "clock_square": Place(
        id="clock_square",
        label="Millennium Clock Square",
        detail="The square had a tall clock, bright banners, and a small stage for songs and stories.",
        hidden="behind the clock face",
    ),
    "harbor": Place(
        id="harbor",
        label="Millennium Harbor",
        detail="The harbor had shining boats, rope bridges, and lanterns tied to every post.",
        hidden="inside a lantern crate",
    ),
    "library": Place(
        id="library",
        label="Millennium Library Hall",
        detail="The hall had high shelves, whisper-quiet corners, and a map wall full of old routes.",
        hidden="under a folded map",
    ),
}

MYSTERIES = {
    "lost_bell": Mystery(
        id="lost_bell",
        clue="a tiny bell sound in the wrong place",
        mistaken_guess="a thief had taken it",
        twist="the bell was tied to a kite string and had drifted up above the square",
        solved_by="listening carefully and looking upward together",
    ),
    "vanishing_map": Mystery(
        id="vanishing_map",
        clue="a map with one corner damp and curled",
        mistaken_guess="someone had hidden the map on purpose",
        twist="a mouse had dragged the map under a warm lamp to make a nest",
        solved_by="following the little paper trail and speaking gently to the mouse",
    ),
    "missing_lantern": Mystery(
        id="missing_lantern",
        clue="a trail of glittering wax drops",
        mistaken_guess="the lantern had been stolen from the feast",
        twist="the lantern was safe in the baker's cart, where the cook had moved it to keep it out of the wind",
        solved_by="asking questions until the cart was found",
    ),
}

GENTLE_OPENERS = [
    "curious",
    "brave",
    "cheerful",
    "lively",
    "patient",
]


def tell(place: Place, mystery: Mystery, hero_name: str, sidekick_name: str) -> World:
    world = World(place, mystery)

    hero = world.add(Entity(id=hero_name, kind="character", type="girl", meters={}, memes={}))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy", meters={}, memes={}))

    hero.memes["wonder"] = 1
    sidekick.memes["wonder"] = 1
    hero.memes["courage"] = 1
    sidekick.memes["courage"] = 1

    world.say(
        f"On the night of the millennium celebration, {hero.id} and {sidekick.id} reached {place.label}."
    )
    world.say(place.detail)
    world.say(
        f"{hero.id} noticed {mystery.clue}, and {sidekick.id} whispered that it might mean {mystery.mistaken_guess}."
    )

    world.para()
    hero.memes["curiosity"] = 1
    sidekick.memes["curiosity"] = 1
    world.say(
        f'"If we walk slowly and ask kind questions, maybe the mystery will tell us where to look," {hero.id} said.'
    )
    world.say(
        f'"Then I will check the lanterns, and you check the corners," {sidekick.id} said, and they split up with careful steps.'
    )

    world.para()
    if mystery.id == "lost_bell":
        world.say(
            f"Near the clock tower, they heard a faint chime, and {hero.id} looked up instead of looking for footprints."
        )
    elif mystery.id == "vanishing_map":
        world.say(
            f"By the map wall, {sidekick.id} found tiny crumbs, so they followed the crumbs instead of the empty shelf."
        )
    else:
        world.say(
            f"By the feast carts, {hero.id} spotted glittering wax drops, so they asked the cook a careful question."
        )

    world.say(
        f"The twist was that {mystery.twist}."
    )

    world.para()
    hero.memes["joy"] = 2
    sidekick.memes["joy"] = 2
    world.say(
        f"{hero.id} laughed in surprise, and {sidekick.id} smiled too. They had been ready for a big problem, but the answer was kind and simple."
    )
    world.say(
        f"Together they solved it by {mystery.solved_by}, and the celebration could go on."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        place=place,
        mystery=mystery,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for children set during a millennium celebration at {f["place"].label}.',
        f"Tell a dialogue-heavy mystery story where {f['hero'].id} and {f['sidekick'].id} solve {f['mystery'].id} with a twist.",
        f'Write a short story with the word "millennium" where two friends ask questions, follow clues, and discover the truth.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    place = f["place"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {sidekick.id} go on the night of the millennium celebration?",
            answer=f"They went to {place.label}, where the celebration lights, stage, and clues were waiting.",
        ),
        QAItem(
            question=f"What clue first made the mystery feel strange?",
            answer=f"The first clue was {mystery.clue}, which made the friends stop and look more closely.",
        ),
        QAItem(
            question=f"What did the friends think was happening at first?",
            answer=f"At first, they thought {mystery.mistaken_guess}. That guess made the mystery feel bigger than it really was.",
        ),
        QAItem(
            question=f"How did the story twist in the end?",
            answer=f"The twist was that {mystery.twist}. That changed the whole story and showed the answer was gentler than they expected.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They solved it by {mystery.solved_by}. Talking, listening, and checking carefully led them to the truth.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does millennium mean?",
            answer="A millennium is a very long time. People often use the word for a celebration or a moment that marks one thousand years.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is puzzling at first. People solve it by noticing clues and asking good questions.",
        ),
        QAItem(
            question="Why do people use dialogue in stories?",
            answer="Dialogue is when characters speak to each other. It helps readers hear their ideas, worries, and plans.",
        ),
        QAItem(
            question="What is an adventure story?",
            answer="An adventure story follows characters as they go somewhere interesting, face a problem, and find a brave way forward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: kind={ent.kind} type={ent.type} meters={ent.meters} memes={ent.memes}")
    lines.append(f"place={world.place.id}")
    lines.append(f"mystery={world.mystery.id}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="clock_square", mystery="lost_bell", hero_name="Mina", sidekick_name="Noah"),
    StoryParams(place="harbor", mystery="missing_lantern", hero_name="Lena", sidekick_name="Eli"),
    StoryParams(place="library", mystery="vanishing_map", hero_name="Asha", sidekick_name="Theo"),
]


ASP_RULES = r"""
place(clock_square).
place(harbor).
place(library).

mystery(lost_bell).
mystery(vanishing_map).
mystery(missing_lantern).

compatible(P, M) :- place(P), mystery(M).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = {(p, m) for p in PLACES for m in MYSTERIES}
    if asp_set == py_set:
        print(f"OK: clingo matches Python ({len(py_set)} combinations).")
        return 0
    print("Mismatch between clingo and Python.")
    print("Only in clingo:", sorted(asp_set - py_set))
    print("Only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A millennium adventure mystery storyworld with dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if args.place and args.mystery:
        if args.place not in PLACES or args.mystery not in MYSTERIES:
            raise StoryError("Unknown place or mystery.")
    choices = [
        (p, m)
        for p in PLACES
        for m in MYSTERIES
        if (args.place is None or p == args.place) and (args.mystery is None or m == args.mystery)
    ]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(choices)
    hero_name = args.name or rng.choice(["Mina", "Lena", "Asha", "Nia", "Ivy"])
    sidekick_name = args.sidekick or rng.choice(["Noah", "Eli", "Theo", "Finn", "Owen"])
    return StoryParams(place=place, mystery=mystery, hero_name=hero_name, sidekick_name=sidekick_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], params.hero_name, params.sidekick_name)
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible place/mystery pairs:\n")
        for place, mystery in combos:
            print(f"  {place:12} {mystery}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
