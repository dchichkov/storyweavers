#!/usr/bin/env python3
"""
storyworlds/worlds/swivel_friendship_magic_inner_monologue_rhyming_story.py
===========================================================================

A standalone storyworld about friendship, a little magic, inner monologue,
and a swivel that changes how two friends solve a problem.

Premise seed:
- A child wants to spin a swivel seat or stool.
- A friend feels left out.
- A small magical trick and an inner thought help them share.
- The story should read like a rhyming, child-facing tiny tale.

The world model tracks:
- physical state: where the swivel object is, who is using it, and whether a
  magical sparkle is active
- emotional state: excitement, worry, jealousy, kindness, shared joy

This is intentionally small and classical: one domain, one turn, one fix.
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
    worn_by: Optional[str] = None
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
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    seat: bool = False


@dataclass
class StoryParams:
    place: str
    prize: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_bits: list[str] = []

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
    "playroom": Place(name="the playroom", indoors=True, affords={"swivel"}),
    "sunroom": Place(name="the sunroom", indoors=True, affords={"swivel"}),
    "porch": Place(name="the porch", indoors=True, affords={"swivel"}),
}

PRIZES = {
    "chair": Prize(label="chair", phrase="a bright little swivel chair", type="chair", seat=True),
    "stool": Prize(label="stool", phrase="a round swivel stool", type="stool", seat=True),
    "bench": Prize(label="bench", phrase="a painted bench with a swivel cushion", type="bench", seat=True),
}

GIRL_NAMES = ["Mia", "Luna", "Nia", "Zoe", "Ruby", "Ada"]
BOY_NAMES = ["Noah", "Finn", "Eli", "Theo", "Max", "Leo"]
PLACES_ORDER = list(PLACES)
PRIZES_ORDER = list(PRIZES)

ASP_RULES = r"""
% A swivel scene is valid when the prize is seat-like and the place affords swivel play.
valid(Place, Prize) :- affords(Place, swivel), seat(Prize).

% Friendship resolution happens when one child notices another child's lonely feeling
% and shares the magic turn.
shared_magic(Place, Prize) :- valid(Place, Prize), affords(Place, swivel).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        if prize.seat:
            lines.append(asp.fact("seat", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((p, r) for p in PLACES for r in PRIZES if PLACES[p].affords and PRIZES[r].seat)
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} valid combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming friendship-and-magic storyworld with a swivel.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
    place = args.place or rng.choice(PLACES_ORDER)
    prize = args.prize or rng.choice(PRIZES_ORDER)
    g1 = args.gender_a or rng.choice(["girl", "boy"])
    g2 = args.gender_b or ("boy" if g1 == "girl" else "girl")
    n1 = args.name_a or rng.choice(GIRL_NAMES if g1 == "girl" else BOY_NAMES)
    n2 = args.name_b or rng.choice(GIRL_NAMES if g2 == "girl" else BOY_NAMES)
    if not PRIZES[prize].seat:
        raise StoryError("The swivel story needs a seat-like prize so the turning can matter.")
    return StoryParams(place=place, prize=prize, name_a=n1, name_b=n2, gender_a=g1, gender_b=g2)


def _make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    a = world.add(Entity(id=params.name_a, kind="character", type=params.gender_a))
    b = world.add(Entity(id=params.name_b, kind="character", type=params.gender_b))
    prize = world.add(Entity(id="swivel", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=a.id))
    a.memes["joy"] = 1.0
    b.memes["worry"] = 0.0
    world.say(f"{a.id} found the swivel seat and gave a grin so bright.")
    world.say(f"{a.id} loved to spin and twirl it, to gleam in morning light.")
    world.say(f"{b.id} came close to watch the fun, with eyes both wide and meek.")
    return world


def _gentle_rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    a = world.get(params.name_a)
    b = world.get(params.name_b)
    prize = world.get("swivel")

    world.para()
    world.say(
        f"One cozy day in {world.place.name}, {a.id} said, \"Come play with me!\" "
        f"{b.id} smiled, but then their heart felt small, and lonely as could be."
    )
    a.memes["curious"] = 1.0
    b.memes["lonely"] = 1.0
    world.say(
        f"{b.id} thought, \"If I just watch from here, will I still get a turn?\""
    )
    world.say(
        f"\"I wish the magic would not hide,\" {b.id} thought, with a little burn."
    )

    world.para()
    a.memes["share"] = 1.0
    a.memes["kind"] = 1.0
    b.memes["hope"] = 1.0
    world.say(
        f"{a.id} heard that quiet inner voice, and knew what it could mean:"
    )
    world.say(
        f"\"A swivel shared is twice the fun, and kindness keeps it clean.\""
    )
    world.say(
        f"{a.id} tapped the seat and whispered low, \"Let's turn with one small spell.\""
    )
    prize.meters["magic"] = 1.0
    world.say(
        f"A silver spark went swish and swam, like bells inside a shell."
    )
    world.say(
        f"The seat went sloooow and soft at first, then spun a gentle ring."
    )

    world.para()
    b.memes["worry"] = 0.0
    b.memes["joy"] = 1.0
    a.memes["joy"] = 2.0
    world.say(
        f"{a.id} scooted over, made a space, and gave {b.id} the chair."
    )
    world.say(
        f"{b.id} sat down, then spun in place, with laughter in the air."
    )
    world.say(
        f"\"Your turn!\" said {a.id}. \"My turn!\" said {b.id}. They went around and round."
    )
    world.say(
        f"Two friends with one enchanted swivel found a happy, twirling ground."
    )

    world.facts.update(
        hero=a,
        friend=b,
        prize=prize,
        place=params.place,
        prize_id=params.prize,
        magic=True,
        shared=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["hero"]
    b = f["friend"]
    return [
        f'Write a short rhyming story for children about two friends named {a.id} and {b.id}, a swivel seat, and a gentle magic surprise.',
        f"Tell a tiny friendship story where {a.id} shares a swivel with {b.id} and an inner thought helps them choose kindness.",
        f'Write a simple magical story that includes the word "swivel" and ends with both friends laughing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["hero"]
    b = f["friend"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who found the swivel seat in {PLACES[place].name}?",
            answer=f"{a.id} found the swivel seat and wanted to spin it first.",
        ),
        QAItem(
            question=f"What did {b.id} feel before the friends shared the seat?",
            answer=f"{b.id} felt lonely at first, because the fun looked close but not yet shared.",
        ),
        QAItem(
            question=f"What did {a.id} do to make the story turn happy?",
            answer=f"{a.id} made room, whispered a little magic, and shared the swivel with {b.id}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with both friends laughing and taking turns on the swivel seat together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does swivel mean?",
            answer="To swivel means to turn around smoothly in a circle or to spin on a seat that can rotate.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and help each other feel happy and safe.",
        ),
        QAItem(
            question="What is a magical sparkle in stories?",
            answer="A magical sparkle is a made-up story sign that something special or surprising is happening.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thinking voice inside their own mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
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
    StoryParams(place="playroom", prize="chair", name_a="Mia", name_b="Noah", gender_a="girl", gender_b="boy"),
    StoryParams(place="sunroom", prize="stool", name_a="Luna", name_b="Theo", gender_a="girl", gender_b="boy"),
    StoryParams(place="porch", prize="bench", name_a="Ada", name_b="Finn", gender_a="girl", gender_b="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid place/prize combos:\n")
        for place, prize in vals:
            print(f"  {place:8} {prize}")
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
            header = f"### {p.name} and {p.name_b}: swivel in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
