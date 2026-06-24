#!/usr/bin/env python3
"""
storyworlds/worlds/prove_happy_ending_mystery.py
================================================

A small mystery storyworld with a child-friendly "prove it" beat and a happy
ending.

Seed tale sketch:
---
A little cat named Miso found a shiny button missing from the basket. Miso and a
kind child searched the room like detectives. They noticed clues: a trail of
thread, a chair pulled back, and a tiny paw print in flour. At last, they proved
who had taken the button: a squirrel who was making a nest from lost things, not
trying to be bad. The squirrel gave the button back, and everyone smiled.

World idea:
---
- Physical meters track clues and object movement.
- Emotional memes track worry, curiosity, relief, trust, and pride.
- The story begins with a mystery, turns on clue-gathering and proof, and ends
  with a gentle happy resolution.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat"}
        male = {"boy", "father", "dad", "man", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    light: str
    clue_kind: str
    missing_item: str
    culprit: str
    culprit_reason: str


@dataclass
class StoryParams:
    place: str
    scene: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


SCENES: dict[str, Scene] = {
    "kitchen": Scene(
        place="the kitchen",
        light="sunny",
        clue_kind="flour",
        missing_item="button",
        culprit="squirrel",
        culprit_reason="it was making a nest from pretty things it found",
    ),
    "attic": Scene(
        place="the attic",
        light="dim",
        clue_kind="dust",
        missing_item="key",
        culprit="mouse",
        culprit_reason="it liked shiny things and dragged them into a cozy hole",
    ),
    "garden": Scene(
        place="the garden shed",
        light="late-afternoon",
        clue_kind="mud",
        missing_item="hat",
        culprit="rabbit",
        culprit_reason="it used the hat to line a warm burrow",
    ),
}

HERO_NAMES = ["Miso", "Nina", "Toby", "Lila", "Ben", "Maya"]
FRIEND_NAMES = ["Pip", "June", "Ollie", "Sana", "Ari", "Zoe"]
HERO_TYPES = ["cat", "dog", "girl", "boy"]
FRIEND_TYPES = ["cat", "dog", "girl", "boy"]
PLACES = ["house", "barn", "cottage", "school"]

ASP_RULES = r"""
% Mystery proof: a clue trail can point to a culprit; enough clues prove it.
clue_trail(P) :- clue(P).
points_to(C, X) :- clue(C), suspect(X), seen_near(C, X).
proof(X) :- suspect(X), clue(door), clue(trail), seen_near(door, X), seen_near(trail, X).
happy_end :- proof(_), returned(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("place", sid, scene.place))
        lines.append(asp.fact("clue_kind", sid, scene.clue_kind))
        lines.append(asp.fact("missing_item", sid, scene.missing_item))
        lines.append(asp.fact("culprit", sid, scene.culprit))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/0."))
    ok = any(sym.name == "happy_end" for sym in model)
    if not ok:
        print("MISMATCH: ASP did not derive happy_end.")
        return 1
    print("OK: ASP derived happy_end.")
    return 0


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny happy-ending mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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
    scene = args.scene or rng.choice(list(SCENES))
    if scene not in SCENES:
        raise StoryError("Unknown scene.")
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        scene=scene,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(HERO_TYPES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        friend_type=args.friend_type or rng.choice(FRIEND_TYPES),
    )


def build_world(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    w = World(scene)

    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = w.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    missing = w.add(Entity(
        id="missing",
        type=scene.missing_item,
        label=scene.missing_item,
        phrase=f"a shiny {scene.missing_item}",
        owner=hero.id,
        caretaker=hero.id,
    ))
    culprit = w.add(Entity(id=scene.culprit, kind="character", type=scene.culprit))
    clue = w.add(Entity(id="clue", type=scene.clue_kind, label=scene.clue_kind))

    w.facts.update(
        hero=hero, friend=friend, missing=missing, culprit=culprit, clue=clue,
        proof=False, happy_end=False,
    )

    hero.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0, "pride": 0.0}
    friend.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0}
    missing.meters = {"lost": 1.0}
    clue.meters = {"seen": 0.0}

    w.say(f"{hero.id} lived near {w.scene.place} and loved quiet days.")
    w.say(f"One {w.scene.light} afternoon, {hero.id} noticed that {hero.pronoun('possessive')} {scene.missing_item} was gone.")
    w.say(f"{friend.id} hurried over and said they should look like detectives.")
    w.para()
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    w.say(f"They searched every corner of {w.scene.place}.")
    w.say(f"Near a table and a little crumb of {scene.clue_kind}, they found a clue trail.")
    clue.meters["seen"] += 1
    w.say(f"{hero.id} pointed and said, \"That clue may help us prove who took the {scene.missing_item}.\"")
    w.para()
    w.say(f"The trail led them to the {scene.culprit}.")
    w.say(f"It did not look mean at all; it looked busy and worried.")
    w.say(f"When they asked, the {scene.culprit} admitted it had taken the {scene.missing_item} because {scene.culprit_reason}.")
    w.say(f"It brought the {scene.missing_item} back right away.")
    missing.carried_by = hero.id
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    friend.memes["relief"] += 1
    w.facts["proof"] = True
    w.facts["happy_end"] = True
    w.para()
    w.say(f"{hero.id} smiled. The mystery was solved, the {scene.missing_item} was safe again, and everybody could breathe easy.")
    w.say(f"At the end, {hero.id} and {friend.id} waved goodbye to the {scene.culprit}, and the room felt kind and peaceful.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, missing, clue = f["hero"], f["friend"], f["missing"], f["clue"]
    return [
        f'Write a short mystery story for a young child that includes the word "prove" and ends happily.',
        f"Tell a gentle detective story where {hero.id} and {friend.id} look for a missing {missing.label} and follow a {clue.label} clue.",
        f"Write a child-friendly mystery with a clear clue trail, a kind culprit, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, missing, culprit, clue = f["hero"], f["friend"], f["missing"], f["culprit"], f["clue"]
    return [
        QAItem(
            question=f"What did {hero.id} want to find in {world.scene.place}?",
            answer=f"{hero.id} wanted to find the missing {missing.label}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {friend.id} solve the mystery?",
            answer=f"A {clue.label} clue helped them follow the trail and learn what happened.",
        ),
        QAItem(
            question=f"Who turned out to have the {missing.label}?",
            answer=f"The {culprit.type} {culprit.id} had it, but only because it was using it for a nest or a cozy home.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and proud because the mystery was solved and the story ended happily.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to prove something?",
            answer="To prove something means to show, with good clues or facts, that it is true.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps detectives figure out what happened.",
        ),
        QAItem(
            question="Why can a mystery still end happily?",
            answer="A mystery can end happily when the missing thing is found and everyone understands what happened.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: proof={world.facts.get('proof')} happy_end={world.facts.get('happy_end')}")
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
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="house", scene="kitchen", hero_name="Miso", hero_type="cat", friend_name="Pip", friend_type="dog"),
    StoryParams(place="cottage", scene="attic", hero_name="Nina", hero_type="girl", friend_name="Ari", friend_type="boy"),
    StoryParams(place="barn", scene="garden", hero_name="Toby", hero_type="dog", friend_name="Zoe", friend_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/0."))
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
