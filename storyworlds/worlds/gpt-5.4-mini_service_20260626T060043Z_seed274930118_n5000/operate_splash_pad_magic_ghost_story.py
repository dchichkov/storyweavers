#!/usr/bin/env python3
"""
A small storyworld for a ghostly splash-pad tale with a touch of magic.

Premise:
- A child visits a splash pad with a friendly ghost.
- They want to operate the water controls and use a magic trick.
- The water can turn spooky-fun if the magic is too wild.
- The story turns when the child learns how to operate the splash pad gently,
  and the ghost helps make the water beautiful instead of scary.

This file follows the Storyweavers world contract:
- standalone stdlib script
- imports shared results eagerly
- imports ASP lazily in ASP helpers
- defines StoryParams, registries, parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    visible: bool = True

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the splash pad"
    affords: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    effect: str
    glow: str
    safe_use: str
    risky_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Operator:
    label: str
    verb: str
    rhythm: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _rule_magic_spark(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    wand = world.entities.get("wand")
    if not ghost or not wand:
        return out
    if ghost.memes.get("magic", 0) < THRESHOLD:
        return out
    if ("spark",) in world.fired:
        return out
    world.fired.add(("spark",))
    ghost.meters["sparkle"] = ghost.meters.get("sparkle", 0) + 1
    out.append("The ghost's magic made the water shimmer like moonlight.")
    return out


def _rule_overwhelm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    if not child or not ghost:
        return out
    if ghost.meters.get("sparkle", 0) < THRESHOLD:
        return out
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    if ("calm",) in world.fired:
        return out
    world.fired.add(("calm",))
    child.memes["worry"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    ghost.memes["pride"] = ghost.memes.get("pride", 0) + 1
    out.append("The child saw it was only sparkle, not danger, and smiled again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_rule_magic_spark, _rule_overwhelm):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"The splash pad gleamed in the sun, with buttons, pipes, and sprinklers waiting."


def introduce(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.traits[0]} {child.type} who loved water days, "
        f"and {ghost.id} was a friendly ghost who liked to drift through shiny places."
    )


def arrive(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"One bright day, {child.id} went to {world.setting.place} with {ghost.id}. "
        f"{setting_detail(world.setting)}"
    )


def wants_operate(world: World, child: Entity, op: Operator) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} wanted to {op.verb}, because the big silver buttons looked like they were "
        f"made for a careful helper."
    )


def ghost_magic(world: World, ghost: Entity, magic: Magic) -> None:
    ghost.memes["magic"] = ghost.memes.get("magic", 0) + 1
    world.say(
        f"{ghost.id} lifted a little {magic.label}, and the tip gave off a soft {magic.glow} glow."
    )


def worry_turn(world: World, child: Entity, magic: Magic, op: Operator) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"Then the water whooshed higher than {child.id} expected, and the ghost's {magic.label} "
        f"made the spray look a bit spooky."
    )
    world.say(
        f"{child.id} stepped back and whispered, 'I hope I can still {op.verb} the right way.'"
    )


def fix_turn(world: World, child: Entity, ghost: Entity, op: Operator, magic: Magic) -> None:
    child.memes["worry"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    ghost.memes["joy"] = ghost.memes.get("joy", 0) + 1
    world.say(
        f"{ghost.id} bobbed gently and showed {child.id} a safer way to {op.verb}: "
        f"one button at a time, and only a tiny bit of {magic.label}."
    )
    world.say(
        f"{child.id} pressed the controls just right, and the spray became a sparkling rainbow mist."
    )


def ending(world: World, child: Entity, ghost: Entity, op: Operator, magic: Magic) -> None:
    world.say(
        f"At the end, {child.id} was happily {op.rhythm}, {ghost.id} was glowing with quiet pride, "
        f"and the splash pad looked magical instead of scary."
    )


SETTING = Setting(place="the splash pad", affords={"operate"})
OPERATE = Operator(
    label="operate the splash pad",
    verb="operate the splash pad",
    rhythm="operating the splash pad buttons",
    risk="too much water",
    fix="a gentle button-by-button rhythm",
    tags={"operate", "water"},
)
MAGIC = Magic(
    id="wand",
    label="magic wand",
    effect="sparkle",
    glow="silver-blue",
    safe_use="a tiny wave",
    risky_use="a wild swirl",
    tags={"magic", "ghost"},
)

CHILD_NAMES = ["Maya", "Nico", "Luna", "Eli", "Iris", "Sam"]
GHOST_NAMES = ["Moss", "Pip", "Boo", "Mimi", "Clover", "Tess"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "careful"]


@dataclass
class StoryParams:
    name: str
    ghost_name: str
    trait: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Maya", "Luna", "Iris"} else "boy",
        traits=[params.trait],
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=params.ghost_name,
        traits=["friendly", "glowing"],
    ))
    wand = world.add(Entity(
        id="wand",
        kind="thing",
        type="wand",
        label="magic wand",
        phrase="a little magic wand",
        owner=ghost.id,
    ))
    world.facts.update(child=child, ghost=ghost, wand=wand, operator=OPERATE, magic=MAGIC)

    introduce(world, child, ghost)
    world.para()
    arrive(world, child, ghost)
    wants_operate(world, child, OPERATE)
    ghost_magic(world, ghost, MAGIC)
    child.memes["worry"] = 1
    propagate(world, narrate=True)
    world.para()
    worry_turn(world, child, MAGIC, OPERATE)
    fix_turn(world, child, ghost, OPERATE, MAGIC)
    ending(world, child, ghost, OPERATE, MAGIC)
    return world


def valid_pairs() -> list[tuple[str, str]]:
    return [("splash pad", "operate")]


def explain_rejection(place: str, action: str) -> str:
    return f"(No story: this world only tells a ghostly tale about trying to {action} at the splash pad.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "splash_pad"))
    lines.append(asp.fact("affords", "splash_pad", "operate"))
    lines.append(asp.fact("operator", "operate"))
    lines.append(asp.fact("magic", "wand"))
    lines.append(asp.fact("ghost_theme", "yes"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, A) :- setting(P), affords(P, A), operator(A), ghost_theme(yes), magic(wand).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_pairs())
    cl = {(p.replace("_", " "), a) for (p, a) in asp_valid_stories()}
    if py == cl:
        print("OK: ASP gate matches Python gate.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost storyworld at a splash pad with a touch of magic.")
    ap.add_argument("--place", choices=["splash pad"])
    ap.add_argument("--activity", choices=["operate"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "splash pad":
        raise StoryError(explain_rejection(args.place, args.activity or "operate"))
    if args.activity and args.activity != "operate":
        raise StoryError(explain_rejection(args.place or "splash pad", args.activity))
    return StoryParams(
        name=rng.choice(CHILD_NAMES),
        ghost_name=rng.choice(GHOST_NAMES),
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    return [
        "Write a short ghost story about a child and a friendly ghost at a splash pad.",
        f"Tell a child-friendly story where {child.id} wants to operate the splash pad while {ghost.label} uses magic.",
        "Write a playful spooky story that ends with the water looking magical, not scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    return [
        QAItem(
            question=f"Who wanted to operate the splash pad?",
            answer=f"{child.id} wanted to operate the splash pad with the friendly ghost {ghost.label} nearby.",
        ),
        QAItem(
            question=f"Why did the water look a little spooky at first?",
            answer=f"It looked spooky because {ghost.label}'s magic made the spray shoot higher and shimmer in a ghostly way.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} operating the buttons gently, so the splash pad turned into a sparkling rainbow scene.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a splash pad?",
            answer="A splash pad is a place with sprinklers and water play where children can run through sprays and puddles.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is often shown as a spooky-looking spirit, but in stories it can also be friendly and helpful.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special power that can make unusual, surprising things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(name="Maya", ghost_name="Boo", trait="curious"),
    StoryParams(name="Nico", ghost_name="Moss", trait="careful"),
    StoryParams(name="Luna", ghost_name="Pip", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        for place, action in stories:
            print(f"{place.replace('_', ' ')} / {action}")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
