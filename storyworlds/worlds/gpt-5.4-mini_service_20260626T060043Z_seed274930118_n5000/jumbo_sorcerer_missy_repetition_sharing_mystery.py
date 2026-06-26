#!/usr/bin/env python3
"""
storyworlds/worlds/jumbo_sorcerer_missy_repetition_sharing_mystery.py
======================================================================

A small mystery storyworld about Missy, a sorcerer, a jumbo object, repeated
clues, and a sharing-based resolution.

The seed tale imagined for this world:
- Missy finds that a jumbo moon lantern is missing from a cozy place.
- A sorcerer helps by repeating clues and sharing tools.
- They follow a few gentle clues, discover the lantern was moved for safety,
  and end with the lantern glowing again in the right spot.

This script keeps the mystery small and state-driven:
- physical meters: hidden, carried, glowing, dusty, wet
- emotional memes: worry, curiosity, trust, relief
- repeated clues matter
- sharing matters
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type == "sorcerer":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit room"
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    missing: str
    clue_style: str
    share_tool: str
    name: str = "Missy"
    seed: Optional[int] = None


SETTINGS = {
    "moonroom": Setting(place="the moonlit room", indoors=True, affordances={"search"}),
    "library": Setting(place="the quiet library", indoors=True, affordances={"search"}),
    "attic": Setting(place="the dusty attic", indoors=True, affordances={"search"}),
    "garden": Setting(place="the lantern garden", indoors=False, affordances={"search"}),
}

MISSING_OBJECTS = {
    "lantern": ("jumbo moon lantern", "a jumbo moon lantern", "lantern", "glow"),
    "key": ("jumbo brass key", "a jumbo brass key", "key", "shine"),
    "book": ("jumbo storybook", "a jumbo storybook", "book", "page"),
}

CLUE_STYLES = {
    "footsteps": {
        "repeat": "The same soft tap-tap tap-tap came again.",
        "find": "tiny footprints",
        "answer": "the tap-tap matched the wheels of a tea cart",
    },
    "whisper": {
        "repeat": "The whisper came again, slow and careful.",
        "find": "a whisper under the door",
        "answer": "the whisper was only the wind moving through a crack",
    },
    "sparkles": {
        "repeat": "The little sparkles showed up again in the dust.",
        "find": "bright sparkles",
        "answer": "the sparkles came from glitter on a scarf",
    },
}

SHARED_TOOLS = {
    "lamp": "a small lamp",
    "rope": "a soft rope",
    "map": "a folded map",
    "mirror": "a little mirror",
}

GIRL_NAMES = ["Missy", "Tia", "Nora", "Lila", "June", "Mina"]
TRAITS = ["curious", "gentle", "patient", "brave"]


# ---------------------------------------------------------------------------
# Narrative world helpers
# ---------------------------------------------------------------------------
def initial_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    missy = world.add(Entity(id="Missy", kind="character", type="girl", label="Missy"))
    sorcerer = world.add(Entity(id="Sorcerer", kind="character", type="sorcerer", label="the sorcerer"))
    label, phrase, thing_type, glow = MISSING_OBJECTS[params.missing]
    missing = world.add(Entity(
        id="MissingObject",
        kind="thing",
        type=thing_type,
        label=label,
        phrase=phrase,
        location=params.place,
    ))
    missing.meters["hidden"] = 1
    missing.meters["glowing"] = 1 if glow == "glow" else 0
    missy.memes["worry"] = 1
    missy.memes["curiosity"] = 1
    sorcerer.memes["trust"] = 1
    world.facts.update(
        missy=missy,
        sorcerer=sorcerer,
        missing=missing,
        clue_style=params.clue_style,
        share_tool=params.share_tool,
    )
    return world


def repeat_clue(world: World, clue_style: str) -> None:
    clue = CLUE_STYLES[clue_style]
    world.say(f"{clue['repeat']} Missy paused and listened again.")
    world.facts["repeated_clue"] = clue["find"]


def share_tool(world: World, tool_id: str) -> None:
    tool_label = SHARED_TOOLS[tool_id]
    missy = world.get("Missy")
    sorcerer = world.get("Sorcerer")
    missy.memes["trust"] += 1
    sorcerer.memes["trust"] += 1
    world.say(
        f"The sorcerer shared {tool_label} with Missy, and Missy shared the
same bright idea right back."
    )
    world.facts["shared_tool"] = tool_label


def search_scene(world: World, clue_style: str, tool_id: str) -> None:
    clue = CLUE_STYLES[clue_style]
    missing = world.get("MissingObject")
    world.say(
        f"Together, Missy and the sorcerer searched the {world.setting.place.removeprefix('the ')} "
        f"for {missing.phrase}."
    )
    repeat_clue(world, clue_style)
    share_tool(world, tool_id)
    world.para()
    world.say(
        f"They followed the {clue['find']} to a small corner, and the sorcerer said the clue "
        f"must be shared with care so nobody rushed past it."
    )
    world.facts["answer_clue"] = clue["answer"]


def resolve(world: World) -> None:
    missing = world.get("MissingObject")
    missy = world.get("Missy")
    sorcerer = world.get("Sorcerer")
    if missing.label.startswith("jumbo moon lantern"):
        missing.meters["hidden"] = 0
        missing.meters["glowing"] = 1
    elif missing.label.startswith("jumbo brass key"):
        missing.meters["hidden"] = 0
        missing.meters["shine"] = 1
    else:
        missing.meters["hidden"] = 0
        missing.meters["safe"] = 1
    missy.memes["worry"] = 0
    missy.memes["relief"] = 1
    sorcerer.memes["relief"] = 1
    world.say(
        f"In the end, they found {missing.phrase} tucked safely where it belonged, not lost at all."
    )
    world.say(
        f"Missy smiled because the repeated clue made sense at last, and sharing the lamp and map had helped them solve the mystery."
    )


def tell(params: StoryParams) -> World:
    world = initial_world(params)
    world.say(
        f"Missy lived in {world.setting.place} where a sorcerer often helped with little mysteries."
    )
    world.say(
        f"One day, {MISSING_OBJECTS[params.missing][1]} was missing, and Missy kept looking at the empty spot with a worried face."
    )
    world.para()
    search_scene(world, params.clue_style, params.share_tool)
    world.para()
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    missing = f["missing"]
    return [
        f'Write a gentle mystery story for a young child about Missy, a sorcerer, and {missing.phrase}.',
        f"Tell a short mystery where a repeated clue and a shared tool help Missy find {missing.phrase}.",
        f'Write a child-friendly story that uses the words "jumbo", "sorcerer", and "Missy" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    missing = f["missing"]
    clue = CLUE_STYLES[f["clue_style"]]
    tool = f["shared_tool"]
    return [
        QAItem(
            question="Who was looking for the missing jumbo thing?",
            answer=f"Missy was looking for {missing.phrase} with the sorcerer.",
        ),
        QAItem(
            question="What clue came again and again?",
            answer=f"{clue['repeat']} The clue they kept hearing was {clue['find']}.",
        ),
        QAItem(
            question="What did they share to help solve the mystery?",
            answer=f"They shared {tool} so they could search carefully together.",
        ),
        QAItem(
            question="What did Missy learn at the end?",
            answer=(
                f"Missy learned that the jumbo object was safe, the repeated clue mattered, "
                f"and sharing helped them solve the mystery."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story about something puzzling that characters try to figure out.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="Why can repeating a clue help?",
            answer="Repeating a clue can help people remember it and notice when it shows up again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid if the setting supports search, the missing object exists,
% the clue style exists, and the shared tool exists.
valid_story(P, M, C, T) :- place(P), missing(M), clue(C), tool(T), affords(P, search).

% The mystery is more story-like when the clue repeats and a sharing action happens.
mystery_shape(P, M, C, T) :- valid_story(P, M, C, T), repeats(C), shares(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", pid, a))
    for mid in MISSING_OBJECTS:
        lines.append(asp.fact("missing", mid))
    for cid in CLUE_STYLES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("repeats", cid))
    for tid in SHARED_TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("shares", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set()
    for p in SETTINGS:
        for m in MISSING_OBJECTS:
            for c in CLUE_STYLES:
                for t in SHARED_TOOLS:
                    if SETTINGS[p].affordances and "search" in SETTINGS[p].affordances:
                        py.add((p, m, c, t))
    cl = set(asp_valid_stories())
    if cl == py:
        print(f"OK: clingo matches Python ({len(cl)} stories).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery world with Missy, a sorcerer, repetition, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--missing", choices=MISSING_OBJECTS)
    ap.add_argument("--clue-style", choices=CLUE_STYLES)
    ap.add_argument("--share-tool", choices=SHARED_TOOLS)
    ap.add_argument("--name", default="Missy")
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
    place = args.place or rng.choice(list(SETTINGS))
    missing = args.missing or rng.choice(list(MISSING_OBJECTS))
    clue_style = args.clue_style or rng.choice(list(CLUE_STYLES))
    share_tool = args.share_tool or rng.choice(list(SHARED_TOOLS))
    return StoryParams(place=place, missing=missing, clue_style=clue_style, share_tool=share_tool, name=args.name)


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
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="moonroom", missing="lantern", clue_style="footsteps", share_tool="map"),
    StoryParams(place="library", missing="book", clue_style="whisper", share_tool="lamp"),
    StoryParams(place="attic", missing="key", clue_style="sparkles", share_tool="mirror"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        for s in stories:
            print(s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
