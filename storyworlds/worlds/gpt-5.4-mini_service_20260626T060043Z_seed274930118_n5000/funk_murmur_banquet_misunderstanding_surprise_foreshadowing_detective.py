#!/usr/bin/env python3
"""
A standalone story world for a small detective tale: a banquet, a murmur, a funk,
and a misunderstanding that ends in a surprise reveal.

The story model is intentionally tiny and constraint-driven:
- A detective notices a strange funk at a banquet.
- Murmurs spread through the room.
- Foreshadowing clues point to the real cause.
- A misunderstanding creates tension.
- A surprise resolution clears the air.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "detective"}
        male = {"boy", "man", "father", "uncle", "chef"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the banquet hall"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    hint: str
    weight: float = 1.0


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    clues_seen: set[str] = field(default_factory=set)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues_seen = set(self.clues_seen)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "banquet_hall": Setting(place="the banquet hall", affords={"banquet"}),
    "garden_room": Setting(place="the garden room", affords={"banquet"}),
}

CHARACTERS = {
    "detective": {"type": "detective", "label": "Detective Iris"},
    "chef": {"type": "chef", "label": "Chef Bram"},
    "host": {"type": "woman", "label": "Mina"},
    "messenger": {"type": "boy", "label": "Toby"},
}

CLUES = {
    "silver_spoon": Clue(
        id="silver_spoon",
        label="a silver spoon",
        kind="silver",
        hint="It caught the candlelight near the soup tureen.",
    ),
    "napkin_note": Clue(
        id="napkin_note",
        label="a napkin note",
        kind="paper",
        hint="A folded napkin had a tiny message tucked inside.",
    ),
    "door_trail": Clue(
        id="door_trail",
        label="a trail by the door",
        kind="dust",
        hint="A faint trail led from the service door to the table.",
    ),
}

CAUSES = {
    "mop_bucket": {
        "label": "a mop bucket",
        "funk": "funk",
        "truth": "the smell came from a mop bucket left too near the dining room",
    },
    "blue_cheese": {
        "label": "a blue cheese plate",
        "funk": "funk",
        "truth": "the smell came from a strong blue cheese plate set out for guests",
    },
}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = "banquet_hall"
    cause: str = "mop_bucket"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def introduce(world: World, detective: Entity, host: Entity, chef: Entity, cause_label: str) -> None:
    world.say(
        f"Detective Iris came to {world.setting.place} just as the guests sat down for a grand banquet."
    )
    world.say(
        f"Mina had invited everyone, and Chef Bram had lined up the plates with careful pride."
    )
    world.say(
        f"Then a strange funk drifted through the room, and the guests began to murmur."
    )
    world.say(
        f"At first, everyone looked at the wrong thing, because the smell made the room feel suspicious."
    )


def clue_line(clue: Clue) -> str:
    return clue.hint


def apply_clue(world: World, clue: Clue) -> None:
    if clue.id in world.clues_seen:
        return
    world.clues_seen.add(clue.id)
    detective = world.get("detective")
    if clue.id == "silver_spoon":
        detective.memes["attention"] = detective.memes.get("attention", 0) + 1
        world.say(
            f"Detective Iris noticed {clue.label} beside the soup, and that was the first foreshadowing clue."
        )
    elif clue.id == "napkin_note":
        world.say(
            f"She found {clue.label}, and the folded paper hinted that someone expected a small mix-up."
        )
    elif clue.id == "door_trail":
        world.say(
            f"Near the door, she found {clue.label}; the line of dust pointed away from the table, not toward it."
        )


def misunderstanding(world: World, detective: Entity, host: Entity, chef: Entity, cause: str) -> None:
    detective.memes["certainty"] = detective.memes.get("certainty", 0) + 1
    world.say(
        f"Detective Iris thought Chef Bram had ruined the banquet, and the room filled with a worried murmur."
    )
    world.say(
        f"Mina frowned too, because she believed the chef had hidden the problem on purpose."
    )
    world.say(
        f"That was the misunderstanding: the wrong person was blamed for the funk."
    )


def surprise_reveal(world: World, detective: Entity, host: Entity, chef: Entity, cause_key: str) -> None:
    cause = CAUSES[cause_key]
    world.say(
        f"Then Detective Iris opened the last clue and smiled, because the foreshadowing finally made sense."
    )
    world.say(
        f'"The funk did not come from Chef Bram," she said. "It came from {cause["truth"]}."'
    )
    world.say(
        f"The guests gasped in surprise, and the whole banquet changed from a worried murmur to relieved laughter."
    )
    world.say(
        f"Mina apologized, Chef Bram straightened his hat, and the banquet hall smelled ordinary again."
    )


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.cause not in CAUSES:
        raise StoryError(f"Unknown cause: {params.cause}")

    world = World(SETTINGS[params.setting])

    detective = world.add(Entity(id="detective", kind="character", type="detective", label="Detective Iris"))
    chef = world.add(Entity(id="chef", kind="character", type="chef", label="Chef Bram"))
    host = world.add(Entity(id="host", kind="character", type="woman", label="Mina"))
    messenger = world.add(Entity(id="messenger", kind="character", type="boy", label="Toby"))

    world.facts["cause"] = CAUSES[params.cause]
    world.facts["detective"] = detective
    world.facts["chef"] = chef
    world.facts["host"] = host
    world.facts["messenger"] = messenger
    world.facts["setting"] = world.setting
    return world


def tell(world: World, params: StoryParams) -> None:
    detective = world.get("detective")
    chef = world.get("chef")
    host = world.get("host")
    cause_label = CAUSES[params.cause]["label"]

    introduce(world, detective, host, chef, cause_label)
    world.para()

    apply_clue(world, CLUES["silver_spoon"])
    apply_clue(world, CLUES["napkin_note"])
    world.say(
        f"The first clue made Detective Iris wonder if the smell was hiding in plain sight."
    )
    world.para()

    misunderstanding(world, detective, host, chef, params.cause)
    world.para()

    apply_clue(world, CLUES["door_trail"])
    surprise_reveal(world, detective, host, chef, params.cause)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    cause = world.facts["cause"]["label"]
    return [
        'Write a short detective story for a young child about a banquet, a funk, and a misunderstanding.',
        f"Tell a gentle mystery where Detective Iris follows clues and solves the problem of {cause}.",
        'Write a simple story that uses the words "funk", "murmur", and "banquet" and ends in a surprise reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    cause = world.facts["cause"]["label"]
    return [
        QAItem(
            question="What strange thing did people notice at the banquet?",
            answer="They noticed a strange funk drifting through the banquet hall, and it made everyone murmur.",
        ),
        QAItem(
            question="Why did Detective Iris think someone was to blame at first?",
            answer="She thought Chef Bram had ruined the banquet, but that was a misunderstanding caused by the confusing smell.",
        ),
        QAItem(
            question="What clue helped Detective Iris solve the mystery?",
            answer="The trail by the door helped her see that the smell came from the wrong place, which led to the surprise ending.",
        ),
        QAItem(
            question="What really caused the funk?",
            answer=f"It really came from {CAUSES[world.facts['cause']['label'].split()[0] if False else 'mop_bucket']['truth'] if False else world.facts['cause']['truth']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banquet?",
            answer="A banquet is a big meal where many people sit together and eat special food.",
        ),
        QAItem(
            question="What does a murmur sound like?",
            answer="A murmur is a soft, low sound of people talking quietly.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people believe the wrong thing or do not understand each other yet.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story drops small clues that help the reader guess what will happen later.",
        ),
        QAItem(
            question="What is a surprise in a mystery story?",
            answer="A surprise is an unexpected answer that changes what everyone thought was true.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(banquet_hall).
setting(garden_room).

affords(banquet_hall,banquet).
affords(garden_room,banquet).

cause(mop_bucket).
cause(blue_cheese).

valid_story(S,C) :- setting(S), cause(C), affords(S,banquet).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple]:
    return [(s, c) for s in SETTINGS for c in CAUSES if "banquet" in SETTINGS[s].affords]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: banquet, murmur, funk, foreshadowing, misunderstanding, surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.cause:
        combos = [c for c in combos if c[1] == args.cause]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, cause = rng.choice(sorted(combos))
    return StoryParams(setting=setting, cause=cause)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:9} ({e.kind:9}) type={e.type}")
    lines.append(f"  clues_seen={sorted(world.clues_seen)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


CURATED = [
    StoryParams(setting="banquet_hall", cause="mop_bucket"),
    StoryParams(setting="garden_room", cause="blue_cheese"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:\n")
        for s, c in combos:
            print(f"  {s:14} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.cause}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
