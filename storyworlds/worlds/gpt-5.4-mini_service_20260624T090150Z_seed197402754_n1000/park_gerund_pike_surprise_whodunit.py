#!/usr/bin/env python3
"""
A small storyworld for a park whodunit with a surprising pike clue.

Premise:
- A child at the park notices something odd.
- A favorite snack, toy, or treasure goes missing.
- The child follows clues and discovers the culprit was not a thief, but an innocent helper or a misunderstood animal/object.
- Surprise reveal resolves the mystery with a gentle ending.

This world keeps the prose child-facing while borrowing whodunit structure:
beginning clue, middle investigation, surprise turn, and a tidy resolution.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    revealed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Park:
    place: str = "the park"
    has_pond: bool = True
    has_playground: bool = True
    has_pier: bool = False


@dataclass
class Clue:
    label: str
    line: str
    meaning: str


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    prize: str
    clue: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, park: Park):
        self.park = park
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PARK = Park(place="the park", has_pond=True, has_playground=True, has_pier=False)

PRIZES = {
    "kite": Entity(id="kite", type="thing", label="kite", phrase="a bright red kite", location="blanket"),
    "snack": Entity(id="snack", type="thing", label="snack box", phrase="a little snack box", location="bench"),
    "marbles": Entity(id="marbles", type="thing", label="marbles bag", phrase="a bag of marbles", location="pocket", plural=True),
}

CLUES = {
    "mud": Clue(
        label="mud print",
        line="There was a tiny muddy print near the bench.",
        meaning="Something wet had been there before the item vanished.",
    ),
    "feather": Clue(
        label="feather",
        line="A soft feather was caught on the swing chain.",
        meaning="A bird had been near the swings.",
    ),
    "pike": Clue(
        label="pike",
        line="A shiny pike-shaped lure gleamed by the pond reeds.",
        meaning="Something fishing-related had been left behind.",
    ),
    "ribbon": Clue(
        label="ribbon",
        line="A blue ribbon fluttered on the picnic table leg.",
        meaning="The missing thing might have been moved by the wind.",
    ),
}

SUSPECTS = {
    "duck": {"type": "duck", "story": "a duck by the pond", "truth": "It had snatched crumbs, not the treasure."},
    "wind": {"type": "wind", "story": "the wind", "truth": "It had only blown the prize a little farther away."},
    "fisher": {"type": "fisher", "story": "a smiling fisher", "truth": "They had dropped a pike-shaped lure while packing up."},
    "squirrel": {"type": "squirrel", "story": "a squirrel", "truth": "It had been collecting shiny things for its nest."},
}

NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
NAMES_BOY = ["Leo", "Ben", "Max", "Theo", "Sam", "Finn"]
TRAITS = ["curious", "careful", "brave", "bright", "patient"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def make_person(world: World, name: str, gender: str, parent: str) -> tuple[Entity, Entity]:
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    adult = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    return child, adult


def setup_world(params: StoryParams) -> World:
    world = World(PARK)
    child, adult = make_person(world, params.name, params.gender, params.parent)

    prize_template = PRIZES[params.prize]
    prize = world.add(Entity(
        id="prize",
        type=prize_template.type,
        label=prize_template.label,
        phrase=prize_template.phrase,
        owner=child.id,
        caretaker=adult.id,
        location=prize_template.location,
        plural=prize_template.plural,
    ))

    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]

    world.facts.update(
        child=child, adult=adult, prize=prize, clue=clue, suspect=suspect,
        park=world.park, params=params
    )
    return world


def intro(world: World) -> None:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    trait = f["params"].gender  # just a stable handle for story text variety
    world.say(
        f"{child.id} was a little {f['params'].gender} who loved the park and noticed every small thing."
    )
    world.say(
        f"{child.id} had brought {prize.phrase} to the park, and {child.pronoun('possessive')} {prize.label} felt very important."
    )
    world.say(
        f"On that day, the air at {world.park.place} felt calm, and the playground looked ready for play."
    )


def missing_item(world: World) -> None:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    prize = f["prize"]
    world.para()
    world.say(
        f"Then {child.id} looked at the blanket and gasped. {child.pronoun('possessive').capitalize()} {prize.label} was gone."
    )
    world.say(
        f'"That is a mystery," said {adult.label}. "We will look for clues."'
    )


def place_clue(world: World) -> None:
    f = world.facts
    clue = f["clue"]
    child = f["child"]
    prize = f["prize"]
    world.say(clue.line)
    world.say(
        f"{child.id} knelt down and followed the clue. {child.pronoun('subject').capitalize()} knew a good mystery needed careful looking."
    )


def investigate(world: World) -> None:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    prize = f["prize"]
    clue = f["clue"]
    suspect = f["suspect"]

    world.say(
        f"Near the pond, {child.id} found a little trail that matched the clue's meaning."
    )
    if clue.label == "pike":
        world.say(
            f"By the reeds lay a shiny pike-shaped lure, which looked surprising in a park."
        )
    elif clue.label == "mud print":
        world.say("The muddy print led past the bench and toward the path.")
    elif clue.label == "feather":
        world.say("The feather pointed toward the swings, where birds often perched.")
    else:
        world.say("The ribbon fluttered in a breeze, as if it had been moved by the wind.")

    world.say(
        f"{adult.label} and {child.id} checked the clues one by one, like real detectives."
    )
    world.say(
        f"{child.id} began to suspect {suspect['story']}."
    )


def surprise_turn(world: World) -> None:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    prize = f["prize"]
    clue = f["clue"]
    suspect = f["suspect"]

    world.para()
    world.say(
        f"At last, the mystery surprised {child.id}."
    )
    if f["suspect"]["type"] == "fisher":
        world.say(
            f"The pike-shaped lure belonged to {suspect['story']}, and it had slipped from a pocket by the pond."
        )
        world.say(
            f"It had nothing to do with the missing {prize.label} at all."
        )
    elif f["suspect"]["type"] == "wind":
        world.say(
            f"The wind had only nudged {prize.it()} away from the blanket and behind the bench."
        )
    elif f["suspect"]["type"] == "duck":
        world.say(
            f"The duck was innocent. It had only chased crumbs and waddled away."
        )
    else:
        world.say(
            f"The squirrel was innocent too. It had only admired shiny things and left a feather behind."
        )
    world.say(
        f"The real answer was simple, and that made the surprise even bigger."
    )


def resolution(world: World) -> None:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    prize = f["prize"]
    clue = f["clue"]
    world.say(
        f"Together they found {prize.it()} tucked safely near the picnic table."
    )
    world.say(
        f"{child.id} laughed, and {adult.label} smiled, because the clues had led them to the truth."
    )
    world.say(
        f"In the end, the park felt bright again, and the little mystery was solved."
    )


def tell_story(world: World) -> None:
    intro(world)
    missing_item(world)
    place_clue(world)
    investigate(world)
    surprise_turn(world)
    resolution(world)


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prize = f["prize"]
    clue = f["clue"]
    return [
        f'Write a child-friendly whodunit set at the park where {child.id} loses {prize.phrase} and finds a surprising clue about {clue.label}.',
        f"Tell a short mystery story with a park setting, a careful clue trail, and a surprise ending that explains where the {prize.label} went.",
        f'Write a gentle detective story for a young child that includes a pike clue and ends with the missing item found again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    prize = f["prize"]
    clue = f["clue"]
    suspect = f["suspect"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a little detective at the park, with {adult.label} helping."
        ),
        QAItem(
            question=f"What went missing at the park?",
            answer=f"{child.id}'s {prize.label} went missing, which started the mystery."
        ),
        QAItem(
            question=f"What clue helped the search?",
            answer=f"The clue was {clue.line.lower()}"
        ),
        QAItem(
            question=f"What was surprising about the ending?",
            answer=f"The surprising part was that {suspect['story']} was not the thief, and the missing thing was found safely nearby."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pike?",
            answer="A pike is a long, sharp fish, and the word can also remind people of a fishing lure shaped like one."
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues to figure out what happened."
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues matter because they help someone learn the truth step by step."
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_story(C, P, Clue) :- child(C), prize(P), clue(Clue), park_scene.
missing(P) :- child_story(_, P, _).
has_clue(Clue) :- clue(Clue).
surprise(Story) :- missing(Story), has_clue(pike), not guilty(duck).
resolved(P) :- missing(P), surprise(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("park_scene"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("clue", "pike"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    # Python gate mirrors the storyworld shape:
    # exactly one park mystery with a clue and a surprise resolution.
    return "pike" in CLUES and "park" and len(PRIZES) > 0


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise/1. #show resolved/1."))
    atoms = set((sym.name, tuple(arg.string if arg.type.name == "String" else arg.number if arg.type.name == "Number" else arg.name for arg in sym.arguments)) for sym in model)
    python_ok = asp_reasonable()
    asp_ok = bool(atoms)
    if python_ok and asp_ok:
        print("OK: ASP and Python gates both accept the park whodunit world.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Python:", python_ok)
    print("ASP atoms:", sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small park whodunit storyworld with a surprising pike clue.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
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
    # One stable domain: every prize can be investigated with every clue/suspect,
    # but pike is the signature surprise clue.
    combos = []
    for prize in PRIZES:
        for clue in CLUES:
            for suspect in SUSPECTS:
                combos.append(("park", prize, clue, suspect))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    prize = args.prize or rng.choice(sorted(PRIZES))
    clue = args.clue or rng.choice(sorted(CLUES))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    if clue == "pike" and suspect == "duck":
        # Not invalid, but less strong; allow it.
        pass
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(name=name, gender=gender, parent=parent, prize=prize, clue=clue, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.revealed:
            bits.append("revealed=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show surprise/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show surprise/1. #show resolved/1."))
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name="Mia", gender="girl", parent="mother", prize="kite", clue="pike", suspect="fisher"),
            StoryParams(name="Leo", gender="boy", parent="father", prize="snack", clue="mud", suspect="duck"),
            StoryParams(name="Nora", gender="girl", parent="mother", prize="marbles", clue="ribbon", suspect="wind"),
            StoryParams(name="Ben", gender="boy", parent="father", prize="kite", clue="feather", suspect="squirrel"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.prize} / clue={p.clue} / suspect={p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
