#!/usr/bin/env python3
"""
A tiny detective-story world about a reader, a tinkerer, and a cockatoo.
The mystery is humorous rather than scary: a missing clue, a noisy bird, and a
small repair that changes who can solve the case.
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

ASP_RULES = r"""
% A story is valid when the detective can use a readable clue, a workable fix,
% and the cockatoo is part of the comic twist.
needs_clue(clue_case) :- clue(clue_case), readable(clue_case).
needs_fix(tool_case) :- broken(tool_case), tinkered(tool_case).
humor_story :- bird(cockatoo), comic_mislead, needs_clue(_), needs_fix(_).
valid_story :- humor_story.
#show valid_story/0.
"""

PLACE_REGISTRY = {
    "library": {
        "label": "the library",
        "tone": "quiet",
        "affords": {"read", "tinker"},
    },
    "workshop": {
        "label": "the workshop",
        "tone": "busy",
        "affords": {"read", "tinker"},
    },
    "porch": {
        "label": "the porch",
        "tone": "sunny",
        "affords": {"read", "tinker"},
    },
}

CASE_REGISTRY = {
    "bookmark": {
        "label": "a bright bookmark",
        "clue": "bookmark",
        "tool": "tape",
        "risk": "lost",
        "fix": "found",
        "detail": "its ribbon tail keeps peeking out from every page",
        "readable": True,
        "tinkerable": False,
        "humor": "the cockatoo kept trying to wear it like a tiny sash",
    },
    "clock": {
        "label": "a small brass clock",
        "clue": "clock",
        "tool": "screwdriver",
        "risk": "stopped",
        "fix": "ticking",
        "detail": "it had one bent hand and a very dramatic tick-tock",
        "readable": False,
        "tinkerable": True,
        "humor": "the cockatoo copied the tick-tock and sounded like a squeaky door",
    },
    "notebook": {
        "label": "a spotted notebook",
        "clue": "notebook",
        "tool": "glue",
        "risk": "ripped",
        "fix": "mended",
        "detail": "a page kept folding open on the same page like it had a secret",
        "readable": True,
        "tinkerable": True,
        "humor": "the cockatoo stepped on the margin and made a claw-print clue",
    },
}

HEROES = ["Mina", "Jules", "Nora", "Theo", "Pip", "Lena", "Arlo", "Ivy"]
SIDEKICKS = ["Moss", "June", "Bea", "Ollie", "Finn", "Rae"]
TRAITS = ["curious", "careful", "brave", "cheerful", "patient", "sharp-eyed"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    case_id: str
    hero: str
    helper: str
    cockatoo_name: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    case: str
    hero: str
    helper: str
    cockatoo: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny humorous detective story world.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--case", choices=CASE_REGISTRY)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=SIDEKICKS)
    ap.add_argument("--cockatoo", choices=["Coco", "Peppy", "Skittles", "Pipkin"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, case) for place in PLACE_REGISTRY for case in CASE_REGISTRY]


def reasonableness_gate(place: str, case_id: str) -> bool:
    return case_id in CASE_REGISTRY and place in PLACE_REGISTRY


def asp_facts() -> str:
    import asp
    lines = []
    for place, meta in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", place))
        lines.append(asp.fact("tone", place, meta["tone"]))
        for a in sorted(meta["affords"]):
            lines.append(asp.fact("affords", place, a))
    for cid, case in CASE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        if case["readable"]:
            lines.append(asp.fact("readable", cid))
        if case["tinkerable"]:
            lines.append(asp.fact("tinkered", cid))
        lines.append(asp.fact("broken", cid))
    lines.append(asp.fact("bird", "cockatoo"))
    lines.append(asp.fact("comic_mislead"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show valid_story/0."), models=1)
    ok = bool(models)
    if ok:
        print("OK: ASP reasoning found a valid humorous detective story.")
        return 0
    print("MISMATCH: no valid ASP story found.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    case = args.case or rng.choice(list(CASE_REGISTRY))
    if not reasonableness_gate(place, case):
        raise StoryError("The chosen place/case combination is not workable.")
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(SIDEKICKS)
    cockatoo = args.cockatoo or rng.choice(["Coco", "Peppy", "Skittles", "Pipkin"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, case=case, hero=hero, helper=helper, cockatoo=cockatoo, trait=trait)


def build_world(params: StoryParams) -> World:
    world = World(params.place, params.case, params.hero, params.helper, params.cockatoo)
    case = CASE_REGISTRY[params.case]
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero, traits=[params.trait]))
    helper = world.add(Entity(id="helper", kind="character", type="child", label=params.helper, traits=["helpful"]))
    bird = world.add(Entity(id="bird", kind="character", type="cockatoo", label=params.cockatoo, traits=["loud", "funny"]))
    clue = world.add(Entity(id="clue", type="object", label=case["label"], phrase=case["label"], owner=hero.id))
    tool = world.add(Entity(id="tool", type="tool", label=case["tool"], phrase=case["tool"], owner=helper.id))
    world.facts.update(hero=hero, helper=helper, bird=bird, clue=clue, tool=tool, case=case, params=params)
    return world


def narrate(world: World) -> None:
    f = world.facts
    hero, helper, bird, clue, tool, case, params = f["hero"], f["helper"], f["bird"], f["clue"], f["tool"], f["case"], f["params"]

    world.say(f"{params.hero} was a {params.trait} little detective who loved to read for clues.")
    world.say(f"{params.helper} liked to tinker with broken things, especially when a mystery needed a tidy fix.")
    world.say(f"One day, a cockatoo named {params.cockatoo} bobbed into {PLACE_REGISTRY[params.place]['label']} and made the whole case feel funny.")
    world.para()

    if case["readable"]:
        world.say(f"{hero.label} opened {clue.label} and read the page carefully.")
    else:
        world.say(f"{hero.label} studied {clue.label}, but the clue was more about tinkering than reading.")
    world.say(f"It had {case['detail']}.")
    world.say(f"Then {bird.label} flapped over, and {case['humor']}.")
    world.para()

    if case["tinkerable"]:
        world.say(f"The clue had gone {case['risk']}, so {helper.label} used {tool.label} to set it right.")
        world.say(f"After a few careful turns, it was {case['fix']} again.")
    else:
        world.say(f"There was nothing to mend, so {helper.label} only nudged the clue back into place.")
    world.say(f"{hero.label} smiled, because the silly bird had hidden the problem in plain sight.")
    world.say(f"In the end, the detective read the last line, the tinkerer fixed the little trouble, and {bird.label} puffed up like it had solved the case itself.")
    world.facts["resolved"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
    prompts = [
        f"Write a humorous detective story about {params.hero} at {params.place} with a cockatoo named {params.cockatoo}.",
        f"Tell a child-friendly mystery where someone must read a clue and tinker with a broken thing.",
        f"Make the cockatoo part of the joke, but let the mystery end with a clear fix.",
    ]
    story_qa = [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {params.hero}, a {params.trait} child who loved to read clues.",
        ),
        QAItem(
            question=f"What did {params.helper} do to help?",
            answer=f"{params.helper} tinkered with the broken clue using a {CASE_REGISTRY[params.case]['tool']}.",
        ),
        QAItem(
            question=f"Why was the cockatoo funny?",
            answer=f"{params.cockatoo} made a silly distraction and turned the mystery into a joke before the clue was solved.",
        ),
    ]
    world_qa = [
        QAItem(question="What does it mean to read a clue?", answer="It means to look closely at words or signs to learn what happened."),
        QAItem(question="What does it mean to tinker?", answer="It means to make small careful repairs or adjustments to something."),
        QAItem(question="What is a cockatoo?", answer="A cockatoo is a noisy parrot with a lively crest and a playful way of moving."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for eid, ent in world.entities.items():
        lines.append(f"{eid}: {ent.type} {ent.label}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, case in valid_combos():
            params = StoryParams(
                place=place,
                case=case,
                hero=HEROES[0],
                helper=SIDEKICKS[0],
                cockatoo="Coco",
                trait=TRAITS[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
