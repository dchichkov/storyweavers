#!/usr/bin/env python3
"""
Standalone storyworld: a gentle ghost story about a child, a surprise, and a
haunted but kind place where laughter goes missing and then returns.

The domain is intentionally small:
- a child enters a quiet old house
- an absent laugh is noticed as a spooky absence
- dialogue with a friendly ghost reveals a surprise
- the ending proves the world changed by bringing back warmth and laughter

Seed words used in-world and in prompts:
- radical
- laugh
- absent
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
    location: str = ""
    friendly: bool = False
    translucent: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    echoes: bool = False
    absorbs_laugh: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _ghostly_absence(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes.get("missing_laugh", 0) >= THRESHOLD and not e.memes.get("noticed", 0):
            e.memes["noticed"] = 1
            out.append(f"{e.id} felt the room's laugh was absent, as if a blanket had gone missing.")
    return out


def _surprise(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.id == "ghost" and e.memes.get("reveal", 0) >= THRESHOLD and not e.memes.get("surprised", 0):
            e.memes["surprised"] = 1
            out.append("A surprise stirred in the dusty air.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for rule in (_ghostly_absence, _surprise):
        produced.extend(rule(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_place(place_id: str) -> Place:
    return PLACES[place_id]


def tell(place: Place, hero_name: str, hero_type: str, ghost_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=ghost_name,
        friendly=True,
        translucent=True,
    ))

    hero.memes["curious"] = 1
    hero.memes["missing_laugh"] = 1
    hero.memes["radical"] = 1

    world.say(
        f"On a quiet night, {hero.id} tiptoed into {place.label}, a place with a radical hush and long shadows on the wall."
    )
    world.say(
        f"{hero.id} liked the old place, but something felt absent. Even the laugh that should have bounced from the corners was gone."
    )

    world.para()
    world.say(
        f'"Hello?" {hero.id} whispered. "Is anyone here?"'
    )
    world.say(
        f'"I am," said {ghost.label}, floating down like a feather. "I was waiting for someone brave enough to notice the silence."'
    )
    hero.memes["wonder"] = 1
    ghost.memes["reveal"] = 1
    propagate(world)

    world.para()
    world.say(
        f'"Why does it feel so empty?" {hero.id} asked.'
    )
    world.say(
        f'"Because my old laugh got tucked away," {ghost.label} said. "I hid it by accident when the clock struck late and the hall went still."'
    )
    world.say(
        f'"That sounds spooky," {hero.id} said, "but also kind of silly."'
    )
    hero.memes["brave"] = 1
    hero.memes["dialogue"] = 1

    world.para()
    world.say(
        f'{hero.id} and {ghost.label} looked behind the piano, under the rug, and inside the umbrella stand.'
    )
    world.say(
        f'At last, {hero.id} found the laugh in a little silver jar with moonlight on its lid.'
    )
    world.say(
        f'"Surprise!" shouted {ghost.label}. "I saved it for a friend."'
    )
    hero.memes["happy"] = 1
    ghost.memes["happy"] = 1
    world.say(
        f'{hero.id} popped the lid, and the laugh flew out in bright little bursts. It sounded warm instead of scary.'
    )
    world.say(
        f'{place.label} stopped feeling absent. It felt full again, with a gentle ghost, a surprised child, and a laugh echoing home.'
    )

    world.facts.update(hero=hero, ghost=ghost, place=place)
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        mood="dusty",
        echoes=True,
        absorbs_laugh=False,
    ),
    "hall": Place(
        id="hall",
        label="the old hall",
        mood="moonlit",
        echoes=True,
        absorbs_laugh=False,
    ),
    "library": Place(
        id="library",
        label="the quiet library",
        mood="soft",
        echoes=False,
        absorbs_laugh=True,
    ),
}

HERO_NAMES = ["Mina", "Owen", "Ivy", "Noah", "Luna", "Eli", "Sara", "Theo"]
GHOST_NAMES = ["Murmur", "Pip", "Moss", "Bramble", "Mallow"]


KNOWLEDGE = {
    "ghost": [
        QAItem(
            question="What is a ghost in a gentle story?",
            answer="In a gentle story, a ghost is a spooky-looking character who may still be kind, lonely, or playful."
        )
    ],
    "laugh": [
        QAItem(
            question="What does a laugh sound like?",
            answer="A laugh sounds bright and bouncy, and it often means something feels funny or happy."
        )
    ],
    "absent": [
        QAItem(
            question="What does absent mean?",
            answer="Absent means not there or missing."
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes someone pause and react with wonder."
        )
    ],
    "radical": [
        QAItem(
            question="What does radical mean in a kid story?",
            answer="In a kid story, radical can mean bold, unusual, or extra exciting."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    ghost = f["ghost"]
    return [
        f"Write a gentle ghost story for a child where {hero.id} explores {place.label} and notices an absent laugh.",
        f"Tell a short story with dialogue and a surprise, featuring {ghost.label} and the word radical.",
        f"Write a spooky-but-kind story about a missing laugh, a friendly ghost, and a happy ending in {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} went to {place.label}, where the air felt quiet and a little spooky."
        ),
        QAItem(
            question=f"Who did {hero.id} meet there?",
            answer=f"{hero.id} met {ghost.label}, a friendly ghost who had hidden the laugh by accident."
        ),
        QAItem(
            question="What was missing at first?",
            answer="At first, the laugh was absent, so the place felt empty and still."
        ),
        QAItem(
            question="What was the surprise?",
            answer="The surprise was that the laugh had been hidden in a silver jar and could be set free again."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the laugh flying out, the ghost smiling, and the place feeling warm again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"ghost", "laugh", "absent", "surprise", "radical"}
    for tag in tags:
        out.extend(KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A place is eerie if it is quiet and can hold an absent laugh.
eerie(P) :- place(P), quiet(P), can_hide_laugh(P).

% The story is valid if there is a hero, a ghost, a surprise, and a laugh that
% moves from absent to present again.
valid_story(Place, Hero, Ghost) :- place(Place), hero(Hero), ghost(Ghost),
                                   absent_laugh(Place),
                                   surprise_event(Place),
                                   restored_laugh(Place).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.echoes:
            lines.append(asp.fact("quiet", pid))
        if place.absorbs_laugh:
            lines.append(asp.fact("can_hide_laugh", pid))
    lines.append(asp.fact("hero_kind", "child"))
    lines.append(asp.fact("ghost_kind", "friendly"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(pid, "child", "friendly") for pid, p in PLACES.items() if p.echoes or p.absorbs_laugh}
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: clingo gate matches Python gate ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if got - expected:
        print("  only in clingo:", sorted(got - expected))
    if expected - got:
        print("  only in python:", sorted(expected - got))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost story world with dialogue and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, hero_name=name, hero_type=gender, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(build_place(params.place), params.hero_name, params.hero_type, params.ghost_name)
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
    StoryParams(place="attic", hero_name="Mina", hero_type="girl", ghost_name="Murmur"),
    StoryParams(place="hall", hero_name="Owen", hero_type="boy", ghost_name="Pip"),
    StoryParams(place="library", hero_name="Ivy", hero_type="girl", ghost_name="Moss"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
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
            header = f"### {p.hero_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
