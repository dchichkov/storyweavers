#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lion_repetition_kindness_ghost_story.py
=====================================================================================================================

A small story world about a lion, a repeating ghostly sound, and a kind
response that changes the night.

Premise seed:
- lion
- repetition
- kindness
- ghost story

The simulated domain is intentionally tiny:
- A little lion hears the same spooky tap-tap three times.
- The lion grows frightened, then notices the ghost is lonely rather than mean.
- Kindness changes the ending: the lion shares a lantern, the ghost repeats a
  softer goodbye, and the night feels safe.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- state-driven narration
- explicit invalid inputs raise StoryError
- inline ASP twin and verification support
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
REPEAT_COUNT = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lion", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    eerie: str
    hides: str


@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    lion = world.get("lion")
    if lion.meters.get("heard_tap", 0.0) < THRESHOLD:
        return out
    if lion.memes.get("fear", 0.0) >= THRESHOLD:
        sig = ("fear_spike",)
        if sig not in world.fired:
            world.fired.add(sig)
            lion.memes["fear"] += 0.5
            out.append("The little lion shivered in the dark.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    lion = world.get("lion")
    ghost = world.get("ghost")
    if lion.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    if ghost.meters.get("company", 0.0) < THRESHOLD:
        sig = ("ghost_warm",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["company"] += 1
            ghost.memes["relief"] += 1
            out.append("The ghost looked less spooky when someone was kind.")
    return out


CAUSAL_RULES = [_r_fear, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(place: Place) -> World:
    world = World(place=place)
    lion = world.add(Entity(
        id="lion",
        kind="character",
        type="lion",
        label="lion",
        traits=["little", "brave", "curious"],
        meters={"heard_tap": 0.0},
        memes={"fear": 0.0, "kindness": 0.0, "curiosity": 0.0, "courage": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="ghost",
        meters={"presence": 0.0, "company": 0.0},
        memes={"lonely": 1.0, "relief": 0.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a small warm lantern",
        owner="lion",
        carried_by="lion",
        meters={"glow": 1.0},
    ))
    world.facts.update(lion=lion, ghost=ghost, lantern=lantern)
    return world


def repeat_tap(world: World, lion: Entity) -> None:
    for i in range(REPEAT_COUNT):
        lion.meters["heard_tap"] += 1
        world.say("Tap. Tap. Tap." if i == 0 else "Tap.")
    lion.memes["fear"] += 1
    propagate(world, narrate=True)


def story_actions(world: World) -> None:
    lion = world.get("lion")
    ghost = world.get("ghost")
    lantern = world.get("lantern")

    world.say(
        f"On a quiet night in {world.place.name}, a little lion walked under the trees "
        f"with {lantern.phrase} in {lion.pronoun('possessive')} paw."
    )
    world.say(
        f"The air felt {world.place.eerie}, and the old path seemed to hide {world.place.hides}."
    )
    world.para()

    repeat_tap(world, lion)
    world.say(
        "Each tap sounded the same, and the same sound made the lion's tail tuck closer to the ground."
    )
    world.say("The lion listened again, because the tapping kept coming back.")
    world.para()

    lion.memes["curiosity"] += 1
    world.say(
        f"Still, {lion.pronoun()} took one careful step and said, "
        f'"Hello? If you are there, I can share my lantern."'
    )
    world.say("That was kindness, not a shout, and the dark waited to see what would happen.")
    lion.memes["kindness"] += 1
    ghost.meters["presence"] += 1
    ghost.memes["lonely"] += -1
    ghost.meters["company"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        "The ghost drifted out from behind the tree. It was not trying to scare anyone. "
        "It only wanted somebody to notice it."
    )
    world.say(
        f"The lion held up {lantern.phrase}, and the warm light made the ghost's edges look soft."
    )
    lion.memes["fear"] = 0.0
    lion.memes["courage"] += 1
    ghost.memes["relief"] += 1
    world.say(
        "The tapping became slower: tap... tap... tap... like a tiny goodbye instead of a warning."
    )
    world.say(
        "The lion and the ghost sat together until the night felt ordinary again."
    )
    world.facts.update(closed=True, repeated=True, kind=True)


def tell(place: Place) -> World:
    world = build_world(place)
    story_actions(world)
    return world


PLACES = {
    "gate": Place(
        name="the garden gate",
        eerie="cool and blue",
        hides="long shadows",
    ),
    "hall": Place(
        name="the old hall",
        eerie="still and dusty",
        hides="echoes",
    ),
    "trees": Place(
        name="the trees behind the house",
        eerie="deep and whispery",
        hides="little glimmers",
    ),
}

CURATED = [
    StoryParams(place="gate"),
    StoryParams(place="hall"),
    StoryParams(place="trees"),
]


def generation_prompts(world: World) -> list[str]:
    place = world.place.name
    return [
        f"Write a short ghost story for young children about a little lion at {place}.",
        "Tell a story where a repeating sound seems scary at first, but kindness changes the ending.",
        f"Write a gentle story about a lion, a ghost, and the same sound coming back again and again at {place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = world.place.name
    return [
        QAItem(
            question=f"Where was the little lion when the tapping kept coming back at {place}?",
            answer=f"The little lion was at {place}, listening to the same tapping sound in the dark.",
        ),
        QAItem(
            question="Why did the lion feel scared at first?",
            answer="The lion felt scared because the tapping sounded spooky when it repeated over and over in the night.",
        ),
        QAItem(
            question="What did the lion say that showed kindness?",
            answer="The lion said it could share the lantern instead of shouting or running away.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The lion and the ghost sat together, and the repeated tapping turned into a soft goodbye instead of something scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character in a story, often shown as something that drifts or glows in the dark.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens again and again, like the same tap or the same word being repeated.",
        ),
        QAItem(
            question="Why does kindness matter?",
            answer="Kindness matters because it helps characters feel safer, calmer, and less alone.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n, *_) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
heard_tap(lion) :- tap(1), tap(2), tap(3).
spooky(lion) :- heard_tap(lion), not kind_reply(lion).
kind_reply(lion) :- says_share_lantern(lion).
ghost_lonely(ghost).
ghost_calm(ghost) :- kind_reply(lion), ghost_lonely(ghost).
ending_safe :- ghost_calm(ghost), heard_tap(lion).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("tap", i) for i in range(1, REPEAT_COUNT + 1)]
    lines.append(asp.fact("ghost_lonely", "ghost"))
    lines.append(asp.fact("says_share_lantern", "lion"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ending_safe/0.\n#show ghost_calm/1.\n#show heard_tap/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    required = {("ending_safe", ()), ("ghost_calm", ("ghost",)), ("heard_tap", ("lion",))}
    if required.issubset(atoms):
        print("OK: ASP twin matches the reasonableness/story skeleton.")
        return 0
    print("MISMATCH in ASP verification.")
    print("atoms:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny lion-and-ghost story world with repetition and kindness.")
    ap.add_argument("--place", choices=PLACES)
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
    return StoryParams(place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place])
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
        print(asp_program("#show ending_safe/0.\n#show ghost_calm/1.\n#show heard_tap/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show ending_safe/0.\n#show ghost_calm/1.\n#show heard_tap/1."))
        print("\n".join(str(a) for a in model))
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
