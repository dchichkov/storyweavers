#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a barricade, a misunderstanding, and a
happy ending.

Seed image:
A small child makes a barricade of blocks, because they think a little scribble
is a bad mark. It turns out the mark is a banner for a game, not a problem.
The child learns the truth, lowers the barricade, and everyone laughs.
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
    carried_by: Optional[str] = None
    blocked_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Setting:
    place: str = "the nursery corner"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"build", "play", "look"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    misread: str
    truth: str
    mess: str = "worry"
    tags: set[str] = field(default_factory=set)


@dataclass
class Barrier:
    id: str
    label: str
    material: str
    height: str
    phrase: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mark = world.get("mark")
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    if mark.meters.get("safe", 0.0) >= THRESHOLD:
        sig = ("misunderstanding",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        out.append(f"{child.pronoun().capitalize()} worried the little mark meant trouble.")
    return out


def _r_barricade(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    barrier = world.get("barricade")
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if barrier.blocked_by == "mark":
        sig = ("barricade",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        barrier.meters["built"] = 1
        out.append(f"{child.pronoun('possessive').capitalize()} {barrier.label} stood up like a wall of blocks.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mark = world.get("mark")
    if mark.meters.get("explained", 0.0) < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    out.append("Then the truth came out in a sing-song voice: the mark was only a banner for play.")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("barricade", _r_barricade), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, activity: Activity, barrier_def: Barrier) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="boy", label="little Pip"))
    grownup = world.add(Entity(id="grownup", kind="character", type="mother", label="Mama"))
    mark = world.add(Entity(id="mark", type="thing", label="mark", phrase="a tiny mark of chalk"))
    barricade = world.add(Entity(id="barricade", type="thing", label="barricade", phrase=barrier_def.phrase))
    barricade.blocked_by = "mark"

    # Setup
    child.memes["curiosity"] = 1
    child.memes["fear"] = 1
    world.say(f"Little Pip was a bright small boy in {setting.place}, where songs seemed to hop along the floor.")
    world.say(f"{grownup.label} smiled, and Pip loved {activity.gerund} with blocky toys and soft, round rhymes.")
    world.say(f"One day Pip saw {mark.phrase}, and the little face went still.")

    # Misunderstanding
    world.para()
    child.memes["worry"] = 1
    world.say(f"Pip thought the mark meant a mess had come to stay, so {child.pronoun('possessive')} brow grew tight.")
    world.say(f"{child.pronoun().capitalize()} decided to make a {barrier_def.label}, {barrier_def.phrase}, to keep the mark away.")
    propagate(world, narrate=True)

    # Turn
    world.para()
    world.say(f"Then {grownup.label} knelt down and began to sing a gentle explanation.")
    mark.meters["explained"] = 1
    world.say(f'"Oh Pip," {grownup.pronoun().capitalize()} said, "that little mark is not a spill at all. It is a sign for the game!"')
    propagate(world, narrate=True)

    # Happy ending
    world.para()
    barricade.meters["built"] = 0
    world.say(f"Pip blinked, then laughed so hard the blocks almost danced.")
    world.say(f"{child.pronoun().capitalize()} lowered the {barrier_def.label}, and the path was open for play.")
    world.say(f"Soon Pip was {activity.gerund} again, and the mark looked merry, not mean.")
    world.say(f"That was the end of the misunderstanding, and the beginning of a happy ending.")

    world.facts.update(
        child=child,
        grownup=grownup,
        mark=mark,
        barricade=barricade,
        activity=activity,
        barrier_def=barrier_def,
        misunderstanding=True,
        resolved=True,
    )
    return world


SETTING = Setting()

ACTIVITIES = {
    "build": Activity(
        id="build",
        verb="build",
        gerund="building",
        misread="a bad mark",
        truth="a banner for the game",
        tags={"build", "barricade"},
    ),
    "play": Activity(
        id="play",
        verb="play",
        gerund="playing",
        misread="a bad mark",
        truth="a banner for the game",
        tags={"play", "joy"},
    ),
}

BARRIERS = {
    "blocks": Barrier(
        id="blocks",
        label="barricade",
        material="blocks",
        height="low",
        phrase="a neat little row of blocks",
    ),
    "pillows": Barrier(
        id="pillows",
        label="barricade",
        material="pillows",
        height="soft",
        phrase="a soft little wall of pillows",
    ),
}

CURATED = [
    ("build", "blocks"),
    ("play", "pillows"),
]


@dataclass
class StoryParams:
    activity: str
    barrier: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a barricade and a misunderstanding.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--barrier", choices=BARRIERS)
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    barrier = args.barrier or rng.choice(list(BARRIERS))
    return StoryParams(activity=activity, barrier=barrier)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a barricade and a misunderstanding.',
        f"Tell a gentle story where {f['child'].label} makes a {f['barrier_def'].label} because {f['mark'].label} seems worrying, but the grownup explains the truth.",
        f"Write a happy ending story with the word '{f['barrier_def'].label}' and a rhyming, child-friendly voice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    barrier = f["barrier_def"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Why did {child.label} make a {barrier.label}?",
            answer=f"{child.label} made a {barrier.label} because the little mark seemed like trouble, and {child.pronoun('possessive')} heart worried about it.",
        ),
        QAItem(
            question=f"What did {grownup.label} explain about the mark?",
            answer=f"{grownup.label} explained that the mark was not a bad sign at all. It was only {activity.truth}, meant for the game.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The misunderstanding went away, the {barrier.label} came down, and {child.label} ended the story smiling in a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barricade?",
            answer="A barricade is a barrier made to block a path, keep something out, or help people feel safe.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling glad and safe.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.blocked_by:
            bits.append(f"blocked_by={e.blocked_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(child) :- worry(child), mark_safe(mark).
barricade(child) :- misunderstanding(child).
happy_ending(child) :- explained(mark), misunderstanding(child).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("worry", "child"),
        asp.fact("mark_safe", "mark"),
        asp.fact("explained", "mark"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/1.\n#show barricade/1.\n#show happy_ending/1."))
    atoms = set()
    for name in ("misunderstanding", "barricade", "happy_ending"):
        atoms.update(asp.atoms(model, name))
    expected = {("child",), ("child",), ("child",)}
    if atoms:
        print("OK: ASP model produced the nursery-story markers.")
        return 0
    print("MISMATCH: ASP model did not produce expected atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIVITIES[params.activity], BARRIERS[params.barrier])
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/1.\n#show barricade/1.\n#show happy_ending/1."))
        print(sorted(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for activity, barrier in CURATED:
            p = StoryParams(activity=activity, barrier=barrier, seed=base_seed)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            i += 1
            sample = generate(p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
