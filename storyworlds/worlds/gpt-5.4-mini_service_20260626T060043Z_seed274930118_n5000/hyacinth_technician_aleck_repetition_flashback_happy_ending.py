#!/usr/bin/env python3
"""
Standalone storyworld: hyacinth, technician, and Aleck.

A small comedy domain built around a technician named Aleck, a stubborn
hyacinth display, a repeated mistake, a short flashback, and a happy ending.
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
# Registries
# ---------------------------------------------------------------------------
LOCATIONS = {
    "greenhouse": "the greenhouse",
    "courtyard": "the courtyard",
    "shop": "the tiny repair shop",
    "garden": "the garden shed",
}

TOOLS = {
    "wrench": "a shiny wrench",
    "notebook": "a grease-smudged notebook",
    "sprayer": "a little water sprayer",
    "ladder": "a wobbly ladder",
}

HYACINTH_STATES = {
    "droopy": "droopy",
    "sparkly": "sparkly",
    "petulant": "petulant",
    "blooming": "blooming",
}

PERSONALITIES = [
    "cheerful",
    "patient",
    "nervous",
    "practical",
    "quirky",
]

FLASHBACK_REASONS = [
    "he had once mixed up the fertilizer labels and sent a whole row of flowers into a sneezy fit",
    "he had already promised the florist he would not let the hyacinths dry out again",
    "he remembered a rainy afternoon when the hyacinths had tipped over and made everyone laugh",
]

SETTINGS = {
    "greenhouse": {
        "place": "the greenhouse",
        "affords": {"repair", "water", "inspect"},
    },
    "courtyard": {
        "place": "the courtyard",
        "affords": {"repair", "water", "inspect"},
    },
    "shop": {
        "place": "the tiny repair shop",
        "affords": {"repair", "inspect"},
    },
    "garden": {
        "place": "the garden shed",
        "affords": {"repair", "water", "inspect"},
    },
}


# ---------------------------------------------------------------------------
# Shared result model
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    tool: str
    hyacinth_state: str
    personality: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def choose_tool(place: str) -> str:
    if place == "shop":
        return "notebook"
    if place == "courtyard":
        return "sprayer"
    if place == "greenhouse":
        return "wrench"
    return "ladder"


def intro(world: World, aleck: Entity, hyacinth: Entity, personality: str) -> None:
    world.say(
        f"Aleck was a {personality} technician who could fix almost anything, "
        f"except when his own ideas started giggling at him."
    )
    world.say(
        f"In {world.place}, he watched a {hyacinth.phrase} named Hyacinth sway on a shelf "
        f"like it was practicing for a tiny dance."
    )


def repetition_bit(world: World, aleck: Entity, hyacinth: Entity) -> None:
    aleck.memes["confidence"] = aleck.memes.get("confidence", 0) + 1
    world.say(
        f"Aleck checked the pot, nodded, and said, 'Easy fix.'"
    )
    world.say(
        f"He said it again: 'Easy fix.'"
    )
    world.say(
        f"Then he said it a third time, which was funny because the hyacinth still looked "
        f"as if it had heard the joke and refused to laugh."
    )
    hyacinth.meters["droop"] = hyacinth.meters.get("droop", 0) + 1


def flashback(world: World, aleck: Entity, reason: str) -> None:
    aleck.memes["memory"] = aleck.memes.get("memory", 0) + 1
    world.say(
        f"That reminded Aleck of an earlier day: {reason}."
    )
    world.say(
        f"He winced, because the memory smelled a little like wet soil and apology."
    )


def mistake(world: World, aleck: Entity, tool: Entity, hyacinth: Entity) -> None:
    aleck.memes["flustered"] = aleck.memes.get("flustered", 0) + 1
    world.say(
        f"He tried the {tool.label} first, then tried the {tool.label} again, and somehow "
        f"the hyacinth looked even more dramatic."
    )
    world.say(
        f"'I meant to help,' Aleck muttered, 'not encourage the flower to become a storm cloud.'"
    )
    hyacinth.meters["dramatic"] = hyacinth.meters.get("dramatic", 0) + 1


def resolve(world: World, aleck: Entity, tool: Entity, hyacinth: Entity) -> None:
    aleck.memes["determination"] = aleck.memes.get("determination", 0) + 1
    hyacinth.meters["water"] = hyacinth.meters.get("water", 0) + 1
    hyacinth.meters["droop"] = 0
    hyacinth.meters["bloom"] = 1
    world.say(
        f"Then Aleck stopped repeating the wrong plan and used the {tool.label} the right way."
    )
    world.say(
        f"He gave the hyacinth a careful drink, straightened the pot, and checked the light."
    )
    world.say(
        f"The flower lifted its face, turned from droopy to blooming, and looked pleased with itself."
    )
    world.say(
        f"Aleck laughed so hard that even the screwdriver on the bench seemed happier."
    )


def ending(world: World, aleck: Entity, hyacinth: Entity) -> None:
    aleck.memes["joy"] = aleck.memes.get("joy", 0) + 1
    world.say(
        f"By the end, Hyacinth stood bright and upright, and Aleck had exactly one successful repair and one excellent story."
    )
    world.say(
        f"He bowed to the flower, and the flower, being a flower, did not bow back, but it did look wonderfully smug."
    )


def build_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]["place"]
    world = World(place=place)
    aleck = world.add(Entity(
        id="Aleck",
        kind="character",
        type="technician",
        label="Aleck",
        phrase="Aleck the technician",
        meters={"work": 1},
        memes={"curiosity": 1},
    ))
    hyacinth = world.add(Entity(
        id="Hyacinth",
        kind="character",
        type="flower",
        label="Hyacinth",
        phrase=f"a {params.hyacinth_state} hyacinth",
        meters={"droop": 1 if params.hyacinth_state != "blooming" else 0, "bloom": 0},
        memes={"mood": 1},
    ))
    tool = world.add(Entity(
        id=params.tool,
        kind="thing",
        type="tool",
        label=TOOLS[params.tool],
        phrase=TOOLS[params.tool],
        owner="Aleck",
    ))

    intro(world, aleck, hyacinth, params.personality)
    world.para()
    repetition_bit(world, aleck, hyacinth)
    flashback(world, aleck, FLASHBACK_REASONS[0])
    mistake(world, aleck, tool, hyacinth)
    world.para()
    resolve(world, aleck, tool, hyacinth)
    ending(world, aleck, hyacinth)

    world.facts.update(
        aleck=aleck,
        hyacinth=hyacinth,
        tool=tool,
        place=params.place,
        personality=params.personality,
        hyacinth_state=params.hyacinth_state,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short comedy about a technician named Aleck, a hyacinth, and a repair that goes funny before it goes right.',
        f"Tell a funny story set in {SETTINGS[f['place']]['place']} where Aleck keeps repeating the same fix and then remembers an earlier mistake.",
        "Write a child-friendly story that includes a flashback, repetition, and a happy ending about a flower and a technician.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Aleck, a technician, and a stubborn hyacinth named Hyacinth.",
        ),
        QAItem(
            question="What did Aleck keep repeating before the repair worked?",
            answer="He kept repeating that it was an easy fix, but repeating it did not help until he changed his plan.",
        ),
        QAItem(
            question="Why did Aleck pause and remember the past?",
            answer="He remembered an earlier mistake with flowers, and that flashback reminded him to be more careful this time.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The hyacinth perked up, Aleck fixed the problem properly, and they both ended the story in a cheerful mood.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a technician?",
            answer="A technician is a person who fixes, checks, or repairs machines, tools, or other things that need careful hands.",
        ),
        QAItem(
            question="What is a hyacinth?",
            answer="A hyacinth is a flower with clustered blossoms and a pleasant smell.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, before returning to the present moment.",
        ),
        QAItem(
            question="Why do repeated mistakes sometimes make a story funny?",
            answer="Repeated mistakes can be funny because the same silly action happens again and again before the character finally changes course.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(greenhouse). place(courtyard). place(shop). place(garden).
tool(wrench). tool(notebook). tool(sprayer). tool(ladder).
personality(cheerful). personality(patient). personality(nervous).
personality(practical). personality(quirky).
state(droopy). state(sparkly). state(petulant). state(blooming).

fixable(P,T) :- place(P), tool(T).
comedy_story(P,T,S) :- fixable(P,T), state(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for s in HYACINTH_STATES:
        lines.append(asp.fact("state", s))
    for per in PERSONALITIES:
        lines.append(asp.fact("personality", per))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show comedy_story/3."))
    return sorted(set(asp.atoms(model, "comedy_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for tool in TOOLS:
            for state in HYACINTH_STATES:
                combos.append((place, tool, state))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about Aleck and a hyacinth.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--state", choices=HYACINTH_STATES)
    ap.add_argument("--personality", choices=PERSONALITIES)
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
    tool = args.tool or choose_tool(place)
    state = args.state or rng.choice(list(HYACINTH_STATES))
    personality = args.personality or rng.choice(PERSONALITIES)
    return StoryParams(place=place, tool=tool, hyacinth_state=state, personality=personality)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:9} ({e.type:10}) meters={e.meters} memes={e.memes}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show comedy_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible comedy combinations:\n")
        for place, tool, state in combos:
            print(f"  {place:10} {tool:10} {state}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for state in HYACINTH_STATES:
                p = StoryParams(place=place, tool=choose_tool(place), hyacinth_state=state, personality="quirky")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
