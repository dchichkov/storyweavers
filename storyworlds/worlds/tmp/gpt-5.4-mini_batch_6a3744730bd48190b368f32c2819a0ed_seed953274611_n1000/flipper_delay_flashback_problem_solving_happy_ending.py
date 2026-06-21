#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flipper_delay_flashback_problem_solving_happy_ending.py
=======================================================================================

A small bedtime-story storyworld about a child, a beloved flipper toy, a delay,
a quick flashback to remember an idea, and a calm problem-solving turn that ends
happily.

The seed premise is simple: bedtime is delayed because something important is
missing. The child remembers, looks back, solves the problem, and gets a cozy
happy ending.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Room:
    id: str
    label: str
    dark: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    missing_place: str
    found_in: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cue:
    id: str
    label: str
    action: str
    why: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        if isinstance(ent, Entity):
            self.entities[ent.id] = ent
        else:
            self.rooms[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities.get(eid) or self.rooms[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.rooms = copy.deepcopy(self.rooms)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    room = world.rooms["bedroom"]
    if child.memes["delay"] >= THRESHOLD and room.meters["worry"] < THRESHOLD:
        room.meters["worry"] += 1
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities["child"]
    if child.meters["solved"] >= THRESHOLD and child.memes["relief"] < THRESHOLD:
        child.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback(world: World, child: Entity, toy: Toy) -> None:
    child.memes["memory"] += 1
    world.say(
        f'{child.id} paused by the bedside and remembered, in a tiny flashback, '
        f'where {toy.label} had been left earlier that day.'
    )
    world.say(
        f'In that little memory, {child.id} saw {toy.label} resting in {toy.found_in}.'
    )


def problem(world: World, child: Entity, parent: Entity, toy: Toy, delay: Cue) -> None:
    child.memes["delay"] += 1
    world.say(
        f'Bedtime had a small delay because {child.id} could not find {toy.label}. '
        f'{parent.label_word.capitalize()} waited by the door with a gentle smile.'
    )
    world.say(
        f'"We can solve this," {parent.id} said softly. '
        f'"First we remember, then we look."'
    )
    world.say(
        f'{delay.why.capitalize()}, so the sleepy room stayed calm instead of upset.'
    )


def solve(world: World, child: Entity, parent: Entity, toy: Toy) -> None:
    child.meters["solved"] += 1
    world.say(
        f'{child.id} tiptoed to {toy.found_in}, looked behind the soft blanket, '
        f'and found {toy.label} right where the memory said it would be.'
    )
    world.say(
        f'{child.id} held up the {toy.label} and smiled. '
        f'"There you are," {parent.id} said, and the worry in the room grew small.'
    )


def bedtime(world: World, child: Entity, parent: Entity, toy: Toy) -> None:
    child.memes["joy"] += 1
    parent.memes["love"] += 1
    world.say(
        f'{parent.id} tucked {child.id} in with {toy.phrase}. '
        f'The lamp glowed warm, the blanket was smooth, and the delay was over.'
    )
    world.say(
        f'{child.id} yawned, hugged {toy.label}, and drifted to sleep with a happy heart.'
    )


def tell(params) -> World:
    world = World()
    child = world.add(Entity(id="Milo", kind="character", type="boy", role="child"))
    parent = world.add(Entity(id="Mom", kind="character", type="mother", role="parent", label="the mom"))
    bedroom = world.add(Room(id="bedroom", label="the bedroom", dark=True))
    toy = TOYS[params.toy]
    cue = CUES[params.cue]

    world.say(
        f'One sleepy night, {child.id} and {parent.id} were getting ready for bed in the bedroom.'
    )
    world.say(
        f'{child.id} wanted to sleep with {toy.label}, because {toy.label} made bedtime feel safe and snug.'
    )
    world.para()
    problem(world, child, parent, toy, cue)
    flashback(world, child, toy)
    solve(world, child, parent, toy)
    world.para()
    bedtime(world, child, parent, toy)

    world.facts.update(
        child=child,
        parent=parent,
        room=bedroom,
        toy=toy,
        cue=cue,
        outcome="happy",
    )
    propagate(world, narrate=False)
    return world


@dataclass
class StoryParams:
    toy: str
    cue: str
    child_name: str = "Milo"
    seed: Optional[int] = None


TOYS = {
    "flipper": Toy(
        id="flipper",
        label="flipper",
        phrase="the little flipper",
        missing_place="under the pillow",
        found_in="the toy basket",
        tags={"flipper", "toy"},
    ),
    "bear": Toy(
        id="bear",
        label="bear",
        phrase="the teddy bear",
        missing_place="by the chair",
        found_in="the blanket pile",
        tags={"bear", "toy"},
    ),
    "boat": Toy(
        id="boat",
        label="boat",
        phrase="the tiny boat",
        missing_place="on the shelf",
        found_in="the toy basket",
        tags={"boat", "toy"},
    ),
}

CUES = {
    "delay": Cue(
        id="delay",
        label="delay",
        action="wait a little longer",
        why="the bedtime delay gave everyone time to think kindly",
        tags={"delay"},
    ),
    "pause": Cue(
        id="pause",
        label="pause",
        action="take a calm pause",
        why="the pause helped the worry settle down",
        tags={"delay"},
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(t, c) for t in TOYS for c in CUES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with flipper, delay, flashback, and problem solving.")
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--cue", choices=CUES)
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
    if args.toy and args.toy not in TOYS:
        raise StoryError("Unknown toy.")
    if args.cue and args.cue not in CUES:
        raise StoryError("Unknown cue.")
    toy = args.toy or rng.choice(sorted(TOYS))
    cue = args.cue or rng.choice(sorted(CUES))
    if (toy, cue) not in valid_combos():
        raise StoryError("(No valid combination matches the given options.)")
    return StoryParams(toy=toy, cue=cue, seed=args.seed)


def generation_prompts(world: World) -> list[str]:
    toy = world.facts["toy"]
    cue = world.facts["cue"]
    return [
        f"Write a bedtime story that includes the words '{toy.label}' and '{cue.label}'.",
        f"Tell a calm story where a child finds a missing {toy.label} after a small {cue.label}.",
        f"Write a story with a flashback, problem solving, and a happy ending about {toy.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    toy = world.facts["toy"]
    return [
        QAItem(
            question="What was missing at bedtime?",
            answer=f"The missing thing was {toy.label}. {child.id} remembered where it had been and found it."
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f'{parent.id} asked for calm thinking, and {child.id} looked back at the memory before checking {toy.found_in}. That careful search solved the delay.'
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {child.id} tucked in and hugging {toy.label} while the room felt warm and safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    toy = world.facts["toy"]
    return [
        QAItem(
            question=f"What is a {toy.label} in this story?",
            answer=f"It is a small beloved toy that helps {world.facts['child'].id} feel safe at bedtime."
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows an earlier memory for a moment. It helps the character remember something important for the problem."
        ),
        QAItem(
            question="Why are bedtime stories often calm and happy?",
            answer="Bedtime stories are often gentle so children can settle down, feel safe, and drift to sleep with a happy thought."
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(meters)} memes={dict(memes)}")
    for r in world.rooms.values():
        lines.append(f"  {r.id:8} (room   ) meters={dict(r.meters)} memes={dict(r.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
happy_end(T) :- toy(T), solve(T), bedtime_done.
delay_event(D) :- cue(D).
problem_solving :- happy_end(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for t in TOYS:
        lines.append(asp.fact("toy", t))
    for c in CUES:
        lines.append(asp.fact("cue", c))
    lines.append(asp.fact("bedtime_done"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show toy/1.\n#show cue/1."))
    toys = [t for (t,) in asp.atoms(model, "toy")]
    cues = [c for (c,) in asp.atoms(model, "cue")]
    return [(t, c) for t in toys for c in cues]


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP combos differ from Python combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(toy=None, cue=None, seed=1), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.toy not in TOYS:
        raise StoryError("Invalid toy.")
    if params.cue not in CUES:
        raise StoryError("Invalid cue.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show toy/1.\n#show cue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for t, c in asp_valid_combos():
            print(f"  {t} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(toy="flipper", cue="delay"),
            StoryParams(toy="bear", cue="pause"),
            StoryParams(toy="boat", cue="delay"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            if p.toy + p.cue in seen:
                continue
            seen.add(p.toy + p.cue)
            samples.append(generate(p))

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
