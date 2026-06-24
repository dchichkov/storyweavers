#!/usr/bin/env python3
"""
dot_friendship_myth.py

A tiny mythic story world about a small dot, a friendship, and a helping sign
that leads two friends back together.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    keeps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name_a: str
    name_b: str
    role_a: str
    role_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "hill": Place(
        id="hill",
        label="the hill of dusk",
        phrase="a high hill where the sky meets the grass",
        keeps={"view", "wind", "echo"},
    ),
    "well": Place(
        id="well",
        label="the old well",
        phrase="an old stone well beside a quiet path",
        keeps={"water", "echo", "shade"},
    ),
    "grove": Place(
        id="grove",
        label="the grove",
        phrase="a little grove of trees that held the moonlight",
        keeps={"shade", "birds", "whisper"},
    ),
}

NAMES = ["Ari", "Mira", "Ivo", "Lena", "Niko", "Sana", "Oren", "Tala"]
ROLES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def valid_place(place: Place) -> bool:
    return "whisper" in place.keeps or "echo" in place.keeps or "view" in place.keeps


def valid_params(p: StoryParams) -> bool:
    return p.name_a != p.name_b


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    a = world.add(Entity(
        id=params.name_a,
        kind="character",
        type=params.role_a,
        label=params.name_a,
        phrase=f"little {params.role_a} {params.name_a}",
        meters={"distance": 0.0},
        memes={"friendship": 1.0, "hope": 1.0},
    ))
    b = world.add(Entity(
        id=params.name_b,
        kind="character",
        type=params.role_b,
        label=params.name_b,
        phrase=f"little {params.role_b} {params.name_b}",
        meters={"distance": 0.0},
        memes={"friendship": 1.0, "hope": 1.0},
    ))
    dot = world.add(Entity(
        id="dot",
        kind="thing",
        type="dot",
        label="dot",
        phrase="a small bright dot",
        owner=a.id,
        location=place.id,
        meters={"glow": 1.0, "size": 1.0},
        memes={"meaning": 1.0},
    ))

    world.facts.update(place=place, a=a, b=b, dot=dot)
    return world


def _stir_longing(world: World) -> None:
    a: Entity = world.facts["a"]  # type: ignore[assignment]
    b: Entity = world.facts["b"]  # type: ignore[assignment]
    dot: Entity = world.facts["dot"]  # type: ignore[assignment]

    a.memes["missing_friend"] = 1.0
    b.memes["missing_friend"] = 1.0
    dot.meters["glow"] += 0.5

    world.say(
        f"Long ago, {a.label} and {b.label} were friends, and they loved to meet "
        f"where the world felt wide."
    )
    world.say(
        f"But one misty morning, they lost sight of each other, and each carried "
        f"a small ache in the chest."
    )
    world.say(
        f"At the same time, the little dot shone on the ground like a patient star."
    )


def _follow_dot(world: World) -> None:
    a: Entity = world.facts["a"]  # type: ignore[assignment]
    b: Entity = world.facts["b"]  # type: ignore[assignment]
    dot: Entity = world.facts["dot"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]

    a.meters["distance"] = 1.0
    b.meters["distance"] = 1.0
    a.memes["curiosity"] = 1.0
    b.memes["curiosity"] = 1.0

    world.say(
        f"{a.label} followed the dot across {place.phrase}, because a friend "
        f"will walk farther when hope is near."
    )
    world.say(
        f"{b.label} saw the same dot from the other side and felt it was a sign "
        f"that someone was still waiting."
    )


def _meet_and_name(world: World) -> None:
    a: Entity = world.facts["a"]  # type: ignore[assignment]
    b: Entity = world.facts["b"]  # type: ignore[assignment]
    dot: Entity = world.facts["dot"]  # type: ignore[assignment]

    a.meters["distance"] = 0.0
    b.meters["distance"] = 0.0
    a.memes["joy"] = 1.0
    b.memes["joy"] = 1.0
    a.memes["friendship"] += 1.0
    b.memes["friendship"] += 1.0
    dot.memes["meaning"] += 1.0
    dot.owner = None

    world.say(
        f"At last they met beside the dot, and their smiles arrived before their words."
    )
    world.say(
        f"They called it the friend-dot, because it had done what a good sign should do: "
        f"bring two hearts to the same place."
    )


def simulate(world: World) -> None:
    _stir_longing(world)
    world.para()
    _follow_dot(world)
    world.para()
    _meet_and_name(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    a: Entity = world.facts["a"]  # type: ignore[assignment]
    b: Entity = world.facts["b"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    return [
        f"Write a short myth about a small dot that helps {a.label} and {b.label} find each other at {place.label}.",
        f"Tell a gentle legend where a tiny dot becomes a sign of friendship and leads two friends home together.",
        f"Write a child-friendly myth about a bright dot, a lonely path, and two friends who remember one another.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a: Entity = world.facts["a"]  # type: ignore[assignment]
    b: Entity = world.facts["b"]  # type: ignore[assignment]
    place: Place = world.facts["place"]  # type: ignore[assignment]
    dot: Entity = world.facts["dot"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who were the two friends in the myth?",
            answer=f"The two friends were {a.label} and {b.label}. They were the ones the little dot helped find each other again.",
        ),
        QAItem(
            question=f"What did the dot do at {place.label}?",
            answer=f"The dot shone like a sign and helped guide the two friends back together at {place.label}.",
        ),
        QAItem(
            question=f"Why did the friends feel happy at the end?",
            answer=f"They felt happy because they met beside the dot, and their friendship became strong again.",
        ),
        QAItem(
            question=f"What did they call the dot when the story ended?",
            answer=f"They called it the friend-dot, because it had brought the two friends to the same place.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a dot?",
        answer="A dot is a tiny round mark or spot. People can use a dot to point, decorate, or help show where something is.",
    ),
    QAItem(
        question="What is friendship?",
        answer="Friendship is the caring bond between friends who help, remember, and enjoy one another.",
    ),
    QAItem(
        question="What does a sign do?",
        answer="A sign gives a message or a clue. It can help someone know where to go or what to do.",
    ),
    QAItem(
        question="What is a myth?",
        answer="A myth is an old story that explains a special idea in a big, memorable way.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_ok(P) :- place(P).
friendship_story(P) :- place_ok(P), keeps(P, view).
friendship_story(P) :- place_ok(P), keeps(P, echo).
friendship_story(P) :- place_ok(P), keeps(P, whisper).
#show friendship_story/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for k in sorted(place.keeps):
            lines.append(asp.fact("keeps", pid, k))
    return "\n".join(lines)


def asp_program(show: str = "#show friendship_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    asp_places = sorted({p[0] for p in asp.atoms(model, "friendship_story")})
    py_places = sorted([pid for pid, place in PLACES.items() if valid_place(place)])
    if asp_places != py_places:
        print("MISMATCH between ASP and Python gates:")
        print("  ASP:", asp_places)
        print("  PY :", py_places)
        return 1
    print(f"OK: ASP and Python gates match ({len(py_places)} places).")
    return 0


# ---------------------------------------------------------------------------
# Rendering / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:7}) " + " ".join(bits))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny myth about a dot and friendship.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--role-a", choices=ROLES)
    ap.add_argument("--role-b", choices=ROLES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    if not valid_place(PLACES[place]):
        raise StoryError("That place does not fit this mythic friendship tale.")

    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([n for n in NAMES if n != name_a])
    role_a = args.role_a or rng.choice(ROLES)
    role_b = args.role_b or rng.choice(ROLES)

    params = StoryParams(
        place=place,
        name_a=name_a,
        name_b=name_b,
        role_a=role_a,
        role_b=role_b,
    )
    if not valid_params(params):
        raise StoryError("The two friends must be different people.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    simulate(world)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        stories = sorted(set(asp.atoms(model, "friendship_story")))
        print(f"{len(stories)} friendship-ready places:")
        for (pid,) in stories:
            print(f"  {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in sorted(PLACES):
            if valid_place(PLACES[place]):
                params = StoryParams(
                    place=place,
                    name_a="Ari",
                    name_b="Mira",
                    role_a="girl",
                    role_b="boy",
                )
                samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
