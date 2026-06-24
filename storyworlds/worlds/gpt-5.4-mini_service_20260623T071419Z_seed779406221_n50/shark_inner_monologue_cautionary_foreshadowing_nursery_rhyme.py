#!/usr/bin/env python3
"""
shark_inner_monologue_cautionary_foreshadowing_nursery_rhyme.py
===============================================================

A tiny nursery-rhyme storyworld about a young shark, a worried grown-up, and
a safer way to play.

The simulated tale leans on:
- inner monologue
- cautionary warning
- foreshadowing
- a gentle nursery-rhyme cadence

The story is state-driven: meters and memes change the narration, and the ending
proves what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"shark", "mother", "father"}:
            if self.type == "shark":
                return {"subject": "they", "object": "them", "possessive": "their"}[case]
            if self.type in {"mother", "father"}:
                return {"subject": "she" if self.type == "mother" else "he",
                        "object": "her" if self.type == "mother" else "him",
                        "possessive": "her" if self.type == "mother" else "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    shark_name: str
    parent_name: str
    place: str
    lure: str
    safe_play: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(shark_name="Nib", parent_name="Mora", place="the blue bay", lure="a shiny kite", safe_play="bubble rings"),
    StoryParams(shark_name="Mink", parent_name="Tala", place="the moon pool", lure="a bright shell", safe_play="seaweed hoops"),
    StoryParams(shark_name="Finn", parent_name="Nara", place="the coral cove", lure="a fluttering ribbon", safe_play="driftwood games"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [("bay", "kite"), ("pool", "shell"), ("cove", "ribbon")]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if world.get("shark").meters["ripple"] >= THRESHOLD and ("foreshadow",) not in world.fired:
        world.fired.add(("foreshadow",))
        out.append("The water got a little hush, as if the tide knew a choice was near.")
    if world.get("shark").memes["worry"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        out.append("The little shark felt a small tight knot in the belly.")
    if world.get("shark").meters["safeplay"] >= THRESHOLD and ("safe",) not in world.fired:
        world.fired.add(("safe",))
        out.append("The sea felt bright and gentle again.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    w = World()
    shark = w.add(Entity(id="shark", kind="character", type="shark", label=params.shark_name,
                         tags={"shark"}))
    parent = w.add(Entity(id="parent", kind="character", type="mother", label=params.parent_name,
                          tags={"parent"}))
    lure = w.add(Entity(id="lure", type="thing", label=params.lure, tags={"lure"}))
    safe = w.add(Entity(id="safe", type="thing", label=params.safe_play, tags={"safe"}))

    shark.meters["ripple"] = 0.0
    shark.meters["safeplay"] = 0.0
    shark.memes["worry"] = 0.0
    shark.memes["curiosity"] = 0.0
    parent.memes["care"] = 1.0

    w.say(f"By {params.place}, there lived a small shark named {shark.label_word}.")
    w.say(f"{shark.label_word} liked to drift and dream, and {shark.pronoun('subject')} hummed a soft little tune.")
    w.say(f"{shark.label_word} peeked at {params.lure}, and in a quiet inner thought {shark.pronoun('subject')} wondered, 'Could I go near it? Would it be fun? Would it be too bold?'")
    w.say(f"Then {parent.label_word} sang, 'Soft fins, slow spins, stay close where safety begins.'")
    w.say(f"At the edge of the water, a thin tide-tickle twirled round a stone, as if warning that the water was not all play.")
    w.para()
    shark.memes["curiosity"] += 1
    shark.meters["ripple"] += 1
    propagate(w)

    w.say(f"{shark.label_word} wanted to chase {lure.label_word}, but the rhyme in the air made the choice feel tricky.")
    w.say(f"In {shark.pronoun('possessive')} head came another little thought: 'If I dart too far, I may miss my way. Better to pause and sway.'")
    w.para()
    shark.memes["worry"] += 1
    propagate(w)

    w.say(f"{parent.label_word} swam closer and said, 'Little shark, heed the sign: near the rough rocks, the water bites. Come back and play a kinder game.'")
    w.say(f"{shark.label_word} listened. {shark.pronoun('subject').capitalize()} let the longing for the lure drift off like foam.")
    shark.meters["safeplay"] += 1
    shark.memes["worry"] = 0.0
    w.para()
    propagate(w)

    w.say(f"So {shark.label_word} and {parent.label_word} made {params.safe_play} round and bright.")
    w.say(f"They spun in a silver ring, gentle as rain, and the old lure stayed far away.")
    w.say(f"At the end, the sea was calm, {shark.label_word} was smiling, and the small shark had found a safer game to keep.")
    w.facts.update(shark=shark, parent=parent, lure=lure, safe=safe, params=params)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a nursery-rhyme style story about a young shark named {p.shark_name} who wants {p.lure} but is warned to stay safe.",
        f"Tell a gentle cautionary tale with foreshadowing and inner monologue in which {p.shark_name} chooses {p.safe_play} instead of getting too close to {p.lure}.",
        f"Write a rhyming, child-friendly shark story set by {p.place} that includes a worried parent and a safer ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    shark = f["shark"]
    parent = f["parent"]
    lure = f["lure"]
    safe = f["safe"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a small shark named {shark.label_word} and {parent.label_word}, who keep one another safe by the water."
        ),
        QAItem(
            question=f"What did {shark.label_word} want near the water?",
            answer=f"{shark.label_word} wanted to go near {lure.label_word}, but the little shark also felt the warning in the tide and slowed down."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {safe.label_word}; {shark.label_word} and {parent.label_word} played a safer game, and the sea grew calm."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What should you do if a warning tells you to stay back from rough water?",
            answer="You should listen and choose a safer place to play. A warning is there to help you avoid a bad choice."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little clue in a story that hints that something important may happen soon."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thinking voice, like the quiet thoughts in their head."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
shark(X) :- entity(X), kind(X, character), type(X, shark).
warning_near(X) :- shark(X), curiosity(X, C), C > 0.
safer_end(X) :- shark(X), safeplay(X, S), S > 0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("entity", "shark"),
        asp.fact("kind", "shark", "character"),
        asp.fact("type", "shark", "shark"),
        asp.fact("entity", "parent"),
        asp.fact("kind", "parent", "character"),
        asp.fact("type", "parent", "mother"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shark/1. #show safer_end/1."))
    ok = bool(model)
    py_ok = True
    if ok != py_ok:
        print("MISMATCH: ASP/Python parity failed")
        return 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: story generation failed")
        return 1
    print("OK: ASP/Python parity and story smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme shark storyworld.")
    ap.add_argument("--shark-name", choices=["Nib", "Mink", "Finn"], dest="shark_name")
    ap.add_argument("--parent-name", choices=["Mora", "Tala", "Nara"], dest="parent_name")
    ap.add_argument("--place", choices=["the blue bay", "the moon pool", "the coral cove"])
    ap.add_argument("--lure", choices=["a shiny kite", "a bright shell", "a fluttering ribbon"])
    ap.add_argument("--safe-play", choices=["bubble rings", "seaweed hoops", "driftwood games"], dest="safe_play")
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
    places = {"the blue bay": "shark", "the moon pool": "shark", "the coral cove": "shark"}
    if args.place and args.place not in places:
        raise StoryError("Invalid place.")
    shark_name = args.shark_name or rng.choice(["Nib", "Mink", "Finn"])
    parent_name = args.parent_name or rng.choice(["Mora", "Tala", "Nara"])
    place = args.place or rng.choice(list(places))
    lure = args.lure or rng.choice(["a shiny kite", "a bright shell", "a fluttering ribbon"])
    safe_play = args.safe_play or rng.choice(["bubble rings", "seaweed hoops", "driftwood games"])
    return StoryParams(shark_name=shark_name, parent_name=parent_name, place=place, lure=lure, safe_play=safe_play)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shark/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show shark/1. #show safer_end/1."))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
