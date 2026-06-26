#!/usr/bin/env python3
"""
Story world: a curious ghost story in a picnic meadow.

A small child visits a picnic meadow and meets a shy ghost. The ghost wants to
play, but everyone worries ghosts are spooky. The child helps the ghost prove it
is friendly by plying a simple game of lantern, blanket, and hiding in plain
sight. The story resolves when curiosity becomes trust.
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

THEME_WORDS = ("ply", "prove")
SETTING_NAME = "the picnic meadow"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = SETTING_NAME
    affords: set[str] = field(default_factory=lambda: {"meet", "play", "lantern", "prove"})


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
    ap = argparse.ArgumentParser(description="A curious ghost story in a picnic meadow.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait")
    ap.add_argument("--ghost-name")
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


NAMES_GIRL = ["Mia", "Nora", "Lina", "Zoe", "Ava"]
NAMES_BOY = ["Eli", "Finn", "Theo", "Noah", "Ben"]
TRAITS = ["curious", "quiet", "brave", "gentle", "cheerful"]
GHOST_NAMES = ["Pip", "Moss", "Wisp", "Dew", "Float"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = args.trait or "curious"
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(name=name, gender=gender, trait=trait, ghost_name=ghost_name)


def _do_play(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    ghost.memes["hope"] = ghost.memes.get("hope", 0) + 1


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "little"]))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost", traits=["shy", "curious"]))
    blanket = world.add(Entity(id="blanket", type="blanket", label="a bright picnic blanket", owner=child.id))
    lantern = world.add(Entity(id="lantern", type="lantern", label="a small lantern", owner=child.id))

    world.say(f"{child.id} went to {world.setting.place} with {blanket.label} and a small lantern.")
    world.say(f"That day, {child.id} was especially {params.trait}, and {child.id} wanted to see who rustled in the grass.")

    world.para()
    world.say(f"Behind a clump of clover, {ghost.id} hovered in the shade, trying not to scare anyone.")
    world.say(f"{ghost.id} wanted to prove it could be friendly, but being a ghost made every hello feel tricky.")

    world.para()
    world.say(f"{child.id} did not run away. Instead, {child.id} asked a careful question and plyingly held up the lantern.")
    world.say(f"The soft light showed {ghost.id}'s round smile, and the blanket made a safe little spot to sit together.")
    _do_play(world, child, ghost)

    world.para()
    world.say(f"To prove it, {ghost.id} copied the child's game: floating over the blanket, then hiding behind a daisy patch, then popping up again with a tiny bow.")
    world.say(f"{child.id} laughed, because the ghost was not trying to frighten anyone at all. It was trying to join in.")

    world.para()
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    ghost.memes["belonging"] = ghost.memes.get("belonging", 0) + 1
    world.say(f"By the end, {child.id} and {ghost.id} were sharing snacks in the picnic meadow.")
    world.say(f"The lantern glowed on the blanket, and {ghost.id} did not feel spooky anymore. It felt like a friend.")
    world.facts = {"child": child, "ghost": ghost, "blanket": blanket, "lantern": lantern}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    return [
        f'Write a gentle story in a "{SETTING_NAME}" about a {child.type} named {child.id} meeting a ghost named {ghost.id}.',
        f"Tell a child-facing ghost story where curiosity helps {child.id} and {ghost.id} become friends.",
        f'Write a short story that uses the words "{THEME_WORDS[0]}" and "{THEME_WORDS[1]}" in a safe, friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    return [
        QAItem(
            question=f"Who went to the picnic meadow with the blanket and lantern?",
            answer=f"{child.id} went to the picnic meadow with a bright picnic blanket and a small lantern.",
        ),
        QAItem(
            question=f"Why did {ghost.id} want to prove something?",
            answer=f"{ghost.id} wanted to prove it could be friendly, because it was a shy ghost and did not want to scare anyone.",
        ),
        QAItem(
            question=f"How did curiosity help the story turn out well?",
            answer=f"{child.id} stayed curious instead of running away, so {child.id} could ask a careful question and meet {ghost.id} kindly.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} and {ghost.id} were sharing snacks together, and the ghost felt like a friend instead of something spooky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a picnic blanket for?",
            answer="A picnic blanket gives people a clean, comfy place to sit on the grass and share food.",
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives off light so people can see better when it is dim outside.",
        ),
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to know more and asking questions about something new.",
        ),
        QAItem(
            question="What does prove mean?",
            answer="To prove something means to show that it is true by what you do.",
        ),
        QAItem(
            question="What does ply mean in a playful story?",
            answer="In a playful story, ply can mean to work at a simple action with care and persistence, like plying a game again and again.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_curious(C) :- child(C).
ghost_friendly(G) :- ghost(G).
good_story(C, G) :- child_curious(C), ghost_friendly(G).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("child", "hero"),
        asp.fact("ghost", "ghost"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        raise StoryError(f"ASP unavailable: {exc}")
    model = asp.one_model(asp_program("#show good_story/2."))
    atoms = set(asp.atoms(model, "good_story"))
    expected = {("hero", "ghost")}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, expected)
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
    StoryParams(name="Mia", gender="girl", trait="curious", ghost_name="Pip"),
    StoryParams(name="Eli", gender="boy", trait="curious", ghost_name="Wisp"),
    StoryParams(name="Nora", gender="girl", trait="gentle", ghost_name="Moss"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
