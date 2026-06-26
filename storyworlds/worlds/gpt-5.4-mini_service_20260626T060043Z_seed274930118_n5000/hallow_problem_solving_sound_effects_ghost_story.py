#!/usr/bin/env python3
"""
A small ghost-story world with sound effects and problem solving.

Seed premise:
- A child hears spooky noises in a hallow tree at dusk.
- A friendly ghost is worried because its lantern has gone dark.
- Together they use the sound clues to solve the mystery and find the fix.

The simulation tracks physical meters and emotional memes, then turns those
state changes into a child-facing story plus grounded Q&A.
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

STORY_KIND = "ghost_story"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("dark", "bright", "lost", "found", "spooky", "dusty", "wet"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "brave", "curious", "relief", "wonder", "care"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    setting_word: str
    has_echo: bool = True
    spooky: bool = True


@dataclass
class Clue:
    sound: str
    source: str
    meaning: str


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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


SETTINGS = {
    "hallow": Place(name="the hallow oak", setting_word="hallow", has_echo=True, spooky=True),
    "attic": Place(name="the dusty attic", setting_word="attic", has_echo=True, spooky=True),
    "garden": Place(name="the moonlit garden", setting_word="garden", has_echo=False, spooky=True),
}

CHILDREN = ["Mina", "Pip", "Luca", "Ivy", "Toby", "Nora"]
GHOSTS = ["Boo", "Moss", "Pale", "Wisp", "Murmur"]
TYPES = ["girl", "boy"]

CLUES = [
    Clue(sound="creak-creak", source="the old branch", meaning="the branch was swaying in the wind"),
    Clue(sound="tap-tap", source="a small pebble", meaning="a pebble was knocking inside the hollow"),
    Clue(sound="whoosh", source="the night wind", meaning="the wind was slipping through the tree"),
    Clue(sound="thump", source="a sleepy owl", meaning="something heavy had landed nearby"),
]

AIDS = {
    "branch": "a bent stick",
    "pebble": "a smooth pebble",
    "leaf": "a dry leaf",
    "glowworm": "a tiny glowworm jar",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with sound effects and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--ghost")
    ap.add_argument("--kind", choices=TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    child_type = args.kind or rng.choice(TYPES)
    child_name = args.name or rng.choice(CHILDREN)
    ghost_name = args.ghost or rng.choice(GHOSTS)
    return StoryParams(place=place, child_name=child_name, child_type=child_type, ghost_name=ghost_name)


def _sound_line(sound: str) -> str:
    return f"{sound}! goes the dark hollow."


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase="a little lantern", owner=ghost.id))
    clue = world.add(Entity(id="clue", type="clue", label="clue", phrase="sound clues"))

    # Setup
    world.say(f"On a quiet night, {child.label} went to {place.name}.")
    world.say(f"The place was called a {place.setting_word}, and it felt spooky but not mean.")
    world.say(f"{ghost.label} floated nearby with {ghost.pronoun('possessive')} little lantern, and the light went out with a tiny pop.")
    ghost.memes["fear"] += 1
    ghost.meters["dark"] += 1
    child.memes["curious"] += 1
    world.facts["place"] = place
    world.facts["child"] = child
    world.facts["ghost"] = ghost
    world.facts["lantern"] = lantern
    world.facts["clue"] = clue

    # Problem and sound clues
    world.para()
    chosen = CLUES[:3]
    for idx, c in enumerate(chosen):
        world.say(_sound_line(c.sound))
        if idx == 0:
            world.say(f"{child.label} listened hard. {c.meaning}.")
        elif idx == 1:
            world.say(f"{ghost.label} pointed at the hollow. {c.meaning}.")
        else:
            world.say(f"{child.label} smiled. {c.meaning}.")
    world.facts["clues"] = chosen

    # Solve
    world.para()
    child.memes["brave"] += 1
    child.memes["wonder"] += 1
    ghost.memes["care"] += 1
    world.say(f"{child.label} said, “Let's solve it together.”")
    world.say(f"{child.label} put {AIDS['branch']} under the dangling lantern hook, then lifted it with care.")
    world.say(f"Tap-tap. The pebble rolled out, and the lantern wick was clear again.")
    lantern.meters["lost"] = 0
    lantern.meters["found"] = 1
    lantern.meters["bright"] = 1
    ghost.meters["dark"] = 0
    ghost.memes["relief"] += 1
    ghost.memes["fear"] = 0
    world.say(f"Fwoom! The lantern glowed gold and soft.")
    world.say(f"{ghost.label} laughed a whispery laugh, and {child.label} laughed too.")
    world.say(f"At the end, the hallow oak was still spooky-looking, but now it felt like a friendly place to listen.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    child: Entity = p["child"]
    ghost: Entity = p["ghost"]
    place: Place = p["place"]
    return [
        f"Write a child-friendly ghost story set at {place.name} that includes the sound words creak-creak, tap-tap, whoosh, and fwoom.",
        f"Tell a short problem-solving story where {child.label} helps {ghost.label} find why a lantern went dark in a {place.setting_word}.",
        f"Make a spooky-but-kind story about listening to sound clues in {place.name} and fixing the problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    child: Entity = p["child"]
    ghost: Entity = p["ghost"]
    place: Place = p["place"]
    lantern: Entity = p["lantern"]
    clues: list[Clue] = p["clues"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who went to {place.name} on the spooky night?",
            answer=f"{child.label} went to {place.name}, and {ghost.label} was there with a little lantern.",
        ),
        QAItem(
            question=f"What problem did {ghost.label} have?",
            answer=f"{ghost.label}'s lantern went out and the dark made {ghost.label} feel worried.",
        ),
        QAItem(
            question="How did the characters solve the problem?",
            answer=f"{child.label} listened to the sound clues, found the pebble, and helped clear the lantern so it could glow again.",
        ),
        QAItem(
            question=f"What sound did the hollow make when the clues started?",
            answer=f"It made sounds like {clues[0].sound}, {clues[1].sound}, and {clues[2].sound}.",
        ),
        QAItem(
            question=f"How did the story end for {lantern.label}?",
            answer=f"The lantern ended bright and warm instead of dark.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hollow tree?",
            answer="A hollow tree has an empty space inside it, like a small room in the trunk.",
        ),
        QAItem(
            question="Why do sound clues help in a mystery?",
            answer="Sound clues help because they can point to what is happening even when you cannot see it.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light so people can see in the dark.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
sound_clue(creak_creak).
sound_clue(tap_tap).
sound_clue(whoosh).
sound_clue(fwoom).

problem(lantern_dark) :- dark(lantern).
fix(lantern_bright) :- found(pebble), clear(wick).

solved(story) :- problem(lantern_dark), fix(lantern_bright).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("dark", "lantern"),
        asp.fact("found", "pebble"),
        asp.fact("clear", "wick"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    ok = bool(asp.atoms(model, "solved"))
    if ok:
        print("OK: ASP gate matches the Python story setup.")
        return 0
    print("MISMATCH: ASP did not derive a solved story.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_places() -> list[str]:
    return list(SETTINGS)


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


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


CURATED = [
    StoryParams(place="hallow", child_name="Mina", child_type="girl", ghost_name="Boo"),
    StoryParams(place="attic", child_name="Pip", child_type="boy", ghost_name="Wisp"),
    StoryParams(place="garden", child_name="Ivy", child_type="girl", ghost_name="Murmur"),
]


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print("solved atoms:", asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_story_params(args, rng)
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
