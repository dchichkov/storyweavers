#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chump_hew_flashback_slice_of_life.py
===============================================================================================================

A small slice-of-life storyworld with a gentle flashback turn.

Premise:
- Chump and Hew spend an ordinary afternoon together.
- A present-day choice brings back a brief memory from before.
- The memory helps them choose a kinder, safer, or tidier way to continue.
- The ending should feel calm and complete, with the world state visibly changed.

The world is intentionally small:
- one setting
- one shared activity
- one little problem
- one flashback memory
- one resolving action

The story engine models physical meters and emotional memes so the prose can be
driven by state rather than by a fixed paragraph template.
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


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def ensure(self, key: str) -> None:
        if key not in self.meters:
            self.meters[key] = 0.0
        if key not in self.memes:
            self.memes[key] = 0.0

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    recovery: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Memory:
    title: str
    cue: str
    detail: str
    effect: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.flashback_used = False
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story.append(text)

    def render(self) -> str:
        return " ".join(self.story)

    def meter(self, eid: str, key: str) -> float:
        e = self.get(eid)
        return e.meters.get(key, 0.0)

    def mood(self, eid: str, key: str) -> float:
        e = self.get(eid)
        return e.memes.get(key, 0.0)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "courtyard": Setting("the courtyard", indoors=False),
    "kitchen": Setting("the kitchen", indoors=True),
    "porch": Setting("the front porch", indoors=False),
    "library_corner": Setting("the library corner", indoors=True),
}

ACTIVITIES = {
    "snack": Activity(
        id="snack",
        verb="share snacks",
        gerund="sharing snacks",
        risk="crumbs",
        recovery="wipe the table",
        tags={"food", "tidy"},
    ),
    "draw": Activity(
        id="draw",
        verb="draw with chalk",
        gerund="drawing with chalk",
        risk="smudges",
        recovery="rinse the chalk tray",
        tags={"art", "messy"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort tiny toys",
        gerund="sorting tiny toys",
        risk="scatter",
        recovery="put every piece back",
        tags={"play", "tidy"},
    ),
}

MEMORIES = {
    "rain": Memory(
        title="the rainy afternoon",
        cue="the rain tapped the window",
        detail="last week, Chump and Hew had rushed inside with damp sleeves and laughed about the puddles",
        effect="Chump remembered that a small pause could keep a cozy moment from becoming a mess",
    ),
    "lost_crayon": Memory(
        title="the missing crayon",
        cue="a broken blue crayon sat near the edge of the table",
        detail="before, Hew had helped Chump look under the rug until they found the lost crayon together",
        effect="Chump remembered that slowing down made it easier to fix little problems",
    ),
    "warm_cookie": Memory(
        title="the warm cookie",
        cue="the smell of a cookie sheet drifting from the oven",
        detail="once, Chump had shared the last cookie with Hew, and both of them had felt happier than if one had kept it alone",
        effect="Chump remembered that sharing could make an ordinary afternoon feel special",
    ),
}

CHUMP_TRAITS = ["careful", "friendly", "small", "thoughtful"]
HEW_TRAITS = ["patient", "cheerful", "steady", "kind"]


@dataclass
class StoryParams:
    place: str
    activity: str
    memory: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).

flashback_needed(A, M) :- activity(A), memory(M).
valid_story(P, A, M) :- setting(P), act(A), memory(M), flashback_needed(A, M).

#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("act", a))
    for m in MEMORIES:
        lines.append(asp.fact("memory", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_stories())
    if py == ap:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - ap:
        print("  only in Python:", sorted(py - ap))
    if ap - py:
        print("  only in ASP:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, m) for p in SETTINGS for a in ACTIVITIES for m in MEMORIES]


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}")
    if params.memory not in MEMORIES:
        raise StoryError(f"Unknown memory: {params.memory}")

    world = World(SETTINGS[params.place])
    chump = world.add(Entity(
        id="Chump",
        kind="character",
        label="Chump",
        type="child",
        traits=["chump"] + CHUMP_TRAITS,
        meters={"focus": 0.0, "mess": 0.0, "care": 0.0},
        memes={"warmth": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    hew = world.add(Entity(
        id="Hew",
        kind="character",
        label="Hew",
        type="child",
        traits=HEW_TRAITS,
        meters={"focus": 0.0, "mess": 0.0, "care": 0.0},
        memes={"warmth": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    world.facts.update(chump=chump, hew=hew, activity=ACTIVITIES[params.activity], memory=MEMORIES[params.memory])
    return world


def generate_story(world: World) -> None:
    act: Activity = world.facts["activity"]  # type: ignore[assignment]
    mem: Memory = world.facts["memory"]  # type: ignore[assignment]
    chump: Entity = world.facts["chump"]  # type: ignore[assignment]
    hew: Entity = world.facts["hew"]  # type: ignore[assignment]

    world.say(f"On an ordinary afternoon, Chump and Hew were at {world.setting.place}.")
    world.say(f"They were busy {act.gerund}, and the little room or path felt calm and familiar.")
    if world.setting.indoors:
        world.say("The place was quiet enough to hear every small rustle and laugh.")
    else:
        world.say("Outside, the day was soft and bright, with room for slow steps and easy talk.")

    # Present tension.
    chump.meters["focus"] += 1
    chump.meters["mess"] += 1
    hew.meters["care"] += 1
    world.say(f"Chump wanted to {act.verb} all at once, but that made {act.risk} start to pile up.")
    world.say(f"Hew looked at the table and reminded Chump that {act.recovery} would be easier than a big cleanup.")

    # Flashback.
    world.say(f"Then something small brought back a flashback: {mem.cue}.")
    world.say(mem.detail + ".")
    world.flashback_used = True
    chump.memes["worry"] += 1
    chump.memes["warmth"] += 1

    # Resolution.
    world.say(f"Chump paused, took a slower breath, and remembered {mem.effect}.")
    world.say(f"So Chump and Hew did it the easy way: they finished {act.gerund}, then {act.recovery}.")
    chump.meters["mess"] = 0.0
    chump.meters["focus"] += 1
    chump.memes["relief"] += 1
    hew.memes["relief"] += 1
    hew.meters["care"] += 1
    world.say(f"When they were done, the spot looked neat again, and the afternoon felt peaceful.")
    world.say(f"Chump and Hew stayed together a little longer, happy that an ordinary moment had turned into a gentle one.")


def story_text(params: StoryParams) -> tuple[World, str]:
    world = build_world(params)
    generate_story(world)
    return world, world.render()


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    act: Activity = world.facts["activity"]  # type: ignore[assignment]
    mem: Memory = world.facts["memory"]  # type: ignore[assignment]
    return [
        f"Write a short slice-of-life story where Chump and Hew are at {world.setting.place} and a flashback helps them finish {act.gerund}.",
        f"Tell a gentle childhood story that includes the word 'chump' and a flashback to {mem.title}.",
        f"Write a calm story about two friends named Chump and Hew who slow down, remember something kind, and tidy up afterward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    act: Activity = world.facts["activity"]  # type: ignore[assignment]
    mem: Memory = world.facts["memory"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who are the two friends in the story?",
            answer="The two friends are Chump and Hew.",
        ),
        QAItem(
            question=f"What were Chump and Hew doing before the flashback?",
            answer=f"They were {act.gerund} at {world.setting.place}.",
        ),
        QAItem(
            question="What brought back the memory?",
            answer=f"{mem.cue.capitalize()}, and that made Chump think about {mem.title}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"Chump and Hew finished {act.gerund}, did the cleanup step, and the place ended neat and peaceful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a brief memory of something that happened before the current moment.",
        ),
        QAItem(
            question="What does it mean to be careful?",
            answer="Being careful means slowing down enough to avoid problems and keep things safe or tidy.",
        ),
        QAItem(
            question="Why do people tidy up after sharing snacks or toys?",
            answer="People tidy up so the space stays nice, and so crumbs, toys, or other little things do not get left behind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: meters={ent.meters} memes={ent.memes} traits={ent.traits}")
    lines.append(f"flashback_used={world.flashback_used}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life flashback storyworld.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--memory", choices=sorted(MEMORIES))
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.memory:
        combos = [c for c in combos if c[2] == args.memory]
    if not combos:
        raise StoryError("No valid story combination matches those options.")
    place, activity, memory = rng.choice(combos)
    return StoryParams(place=place, activity=activity, memory=memory)


def generate(params: StoryParams) -> StorySample:
    world, story = story_text(params)
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="courtyard", activity="snack", memory="warm_cookie"),
    StoryParams(place="kitchen", activity="draw", memory="lost_crayon"),
    StoryParams(place="porch", activity="sort", memory="rain"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print("  ", item)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
