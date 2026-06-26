#!/usr/bin/env python3
"""
A small mystery storyworld about a suspicious punt, a hidden clue, and a twist.

The domain is deliberately tiny and state-driven:
- one child detective
- one punt boat on a quiet pond
- a missing object
- a clue that changes the meaning of the scene
- a twist resolution that explains the mystery

The prose should read like a complete tiny mystery, with a beginning, a middle
turn, and an ending image that proves what changed.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    near_water: bool
    affords_punt: bool = True


@dataclass
class Twist:
    id: str
    reveal: str
    clue: str
    culprit_type: str
    reason: str


@dataclass
class StoryParams:
    place: str
    twist: str
    name: str
    gender: str
    guardian: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, twist: Twist) -> None:
        self.place = place
        self.twist = twist
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy as _copy
        c = World(self.place, self.twist)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "pond": Place(name="the pond", near_water=True),
    "canal": Place(name="the canal", near_water=True),
    "marsh": Place(name="the marsh", near_water=True),
}

TWISTS = {
    "lost_key": Twist(
        id="lost_key",
        clue="a tiny brass key",
        reveal="it was not stolen at all; it had slipped under the punt seat",
        culprit_type="seat",
        reason="the water moved the boat, and the key slid into a hidden crack",
    ),
    "mud_print": Twist(
        id="mud_print",
        clue="a muddy print",
        reveal="the muddy print belonged to the dog, not to a thief",
        culprit_type="dog",
        reason="the dog jumped aboard after sniffing the fish basket",
    ),
    "ribbon": Twist(
        id="ribbon",
        clue="a blue ribbon",
        reveal="the ribbon was left by the helpful neighbor who had tied the boat loose",
        culprit_type="neighbor",
        reason="the knot had been untied by a gust of wind",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Luna", "Maya", "Tessa", "Ada", "Rose"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Leo", "Eli", "Noah", "Max", "Owen"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(place: Place, twist: Twist) -> bool:
    return place.near_water and bool(twist.clue) and bool(twist.reveal)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for tid, tw in TWISTS.items():
            if valid_story(place, tw):
                out.append((pid, tid))
    return out


def explain_rejection(place: Place, twist: Twist) -> str:
    return (
        f"(No story: {place.name} does not fit this mystery twist well enough.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    twist = TWISTS[params.twist]
    world = World(place, twist)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"curiosity": 0.0},
        memes={"worry": 0.0, "joy": 0.0, "certainty": 0.0},
    ))
    guardian = world.add(Entity(
        id="Guardian",
        kind="character",
        type=params.guardian,
        label=f"the {params.guardian}",
        meters={"worry": 0.0},
        memes={"worry": 0.0},
    ))
    punt = world.add(Entity(
        id="Punt",
        kind="thing",
        type="boat",
        label="punt",
        phrase="a small flat punt",
        meters={"rock": 0.0},
        memes={"mystery": 0.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        kind="thing",
        type="clue",
        label=twist.clue,
        phrase=f"the clue, {twist.clue}",
        meters={"hidden": 1.0},
        memes={"importance": 1.0},
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was a little curious {hero.type} who loved solving small mysteries."
    )
    world.say(
        f"One quiet day, {hero.id} and {guardian.label_word if hasattr(guardian, 'label_word') else guardian.label} "
        f"went to {place.name}, where a punt sat by the water."
    )
    world.say(
        f"{hero.id} noticed that something seemed off about the punt, as if the boat were hiding a secret."
    )

    # Act 2: tension
    world.para()
    hero.memes["worry"] += 1
    hero.meters["curiosity"] += 1
    punt.memes["mystery"] += 1
    world.say(
        f"{hero.id} looked closer and found {twist.clue} near the punt seat."
    )
    world.say(
        f"{hero.id} thought someone had taken it, and {hero.pronoun('possessive')} worry grew."
    )
    guardian.memes["worry"] += 1
    world.say(
        f"But the {params.guardian} asked {hero.id} to slow down and look again."
    )

    # Twist turn
    world.para()
    world.say(
        f"Then the twist came: {twist.reveal}."
    )
    world.say(
        f"{twist.reason.capitalize()}."
    )
    hero.memes["certainty"] += 1
    hero.memes["worry"] = 0.0

    # Resolution
    world.para()
    world.say(
        f"{hero.id} smiled, because the mystery had an answer after all."
    )
    world.say(
        f"{hero.id} tucked the little {twist.clue} safely into a pocket, and the punt looked calm again on the water."
    )
    world.say(
        f"By the end, the quiet pond felt less spooky, and {hero.id} had turned a worry into a solved clue."
    )

    world.facts.update(
        hero=hero,
        guardian=guardian,
        punt=punt,
        clue=clue,
        place=place,
        twist=twist,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    twist = f["twist"]
    return [
        f'Write a short mystery story for a young child about a punt at {place.name}.',
        f"Tell a gentle mystery where {hero.id} finds {twist.clue} near a punt and learns a surprising twist.",
        f'Write a tiny story that includes the word "punt" and ends with a clue being explained.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    place = f["place"]
    twist = f["twist"]
    return [
        QAItem(
            question=f"Who is the mystery story about?",
            answer=f"It is about {hero.id}, a curious child who tries to solve a small mystery at {place.name}.",
        ),
        QAItem(
            question=f"What strange thing did {hero.id} find near the punt?",
            answer=f"{hero.id} found {twist.clue} near the punt seat.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {guardian.type}?",
            answer=f"They understood the clue, the worry faded, and the punt by the water looked ordinary again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a punt?",
            answer="A punt is a flat boat that can float on calm water.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="Why do mysteries use twists?",
            answer="A twist is a surprise that changes what the reader thinks is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
twist(T) :- twist_fact(T).

valid(P,T) :- place(P), twist(T), near_water(P), clue(T), reveal(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        if p.near_water:
            lines.append(asp.fact("near_water", pid))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist_fact", tid))
        lines.append(asp.fact("clue", tid))
        lines.append(asp.fact("reveal", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    try:
        asp_set = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with a punt and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.place and args.twist:
        if (args.place, args.twist) not in combos:
            raise StoryError(explain_rejection(PLACES[args.place], TWISTS[args.twist]))
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.twist is None or c[1] == args.twist)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, twist = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    guardian = args.guardian or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, twist=twist, name=name, gender=gender, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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
    StoryParams(place="pond", twist="lost_key", name="Mina", gender="girl", guardian="mother"),
    StoryParams(place="canal", twist="mud_print", name="Theo", gender="boy", guardian="father"),
    StoryParams(place="marsh", twist="ribbon", name="Ivy", gender="girl", guardian="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible (place, twist) combos:\n")
        for place, twist in asp_valid_combos():
            print(f"  {place:8} {twist}")
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
            header = f"### {p.name}: {p.place} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
