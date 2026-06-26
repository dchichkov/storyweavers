#!/usr/bin/env python3
"""
Storyworld: topic guest mystery to solve, in a nursery-rhyme style.

A small classical simulation about a guest arriving at a cozy home, noticing
a missing nursery-rhyme prop, and helping solve the little mystery through
clues in the world state.
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

DEFAULT_TOPIC = "topic"
DEFAULT_GUEST = "guest"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the nursery"
    indoors: bool = True
    topic: str = DEFAULT_TOPIC


@dataclass
class Mystery:
    id: str
    label: str
    missing: str
    clue_kind: str
    likely_hider: str
    solved_by: str
    rhyme_line: str


@dataclass
class StoryParams:
    topic: str
    guest: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        other = World(self.setting, self.mystery)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, topic="toy"),
    "garden": Setting(place="the garden gate", indoors=False, topic="flower"),
    "kitchen": Setting(place="the kitchen", indoors=True, topic="spoon"),
}

GUESTS = {
    "rabbit": dict(type="rabbit", label="a rabbit guest", phrase="a bright little rabbit"),
    "girl": dict(type="girl", label="a girl guest", phrase="a cheerful little girl"),
    "boy": dict(type="boy", label="a boy guest", phrase="a merry little boy"),
    "cat": dict(type="cat", label="a cat guest", phrase="a soft gray cat"),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        label="the tiny bell",
        missing="gone from the shelf",
        clue_kind="sparkles",
        likely_hider="under the rug",
        solved_by="a ribbon",
        rhyme_line="The bell had a jingle, a tinkle, a ring, but no one could find it anywhere.",
    ),
    "spoon": Mystery(
        id="spoon",
        label="the silver spoon",
        missing="missing from the bowl",
        clue_kind="crumbs",
        likely_hider="behind the chair",
        solved_by="a spoon rest",
        rhyme_line="The spoon was a-sleeping, away from its place, and crumbs made a narrow clue.",
    ),
    "star": Mystery(
        id="star",
        label="the paper star",
        missing="lost from the curtain",
        clue_kind="glitter",
        likely_hider="inside the storybook",
        solved_by="a string loop",
        rhyme_line="The star had gone twinkly, away with the light, and glitter still clung to the clue.",
    ),
}

TOPIC_TO_MYSTERY = {
    "topic": "bell",
    "guest": "spoon",
    "song": "star",
}

NAMES = ["Nina", "Milo", "Pippa", "Toby", "Luna", "Owen", "Bella", "Finn"]


def rhyme_opening(guest: Entity, setting: Setting, mystery: Mystery) -> str:
    return (
        f"Over in {setting.place}, where the soft lamps glow, "
        f"{guest.phrase} came trotting nice and slow."
    )


def rhyme_conflict(guest: Entity, mystery: Mystery, setting: Setting) -> str:
    return (
        f"But hush, in {setting.place}, there was trouble today: "
        f"{mystery.label} was missing and hidden away."
    )


def rhyme_clue(mystery: Mystery) -> str:
    return (
        f"Near a little {mystery.clue_kind} trail, the clue shone bright, "
        f"like a wink in the corners of low candle-light."
    )


def rhyme_solution(guest: Entity, mystery: Mystery, helper: Entity) -> str:
    return (
        f"{guest.id} peeped where {mystery.likely_hider} might be, "
        f"then found {mystery.label} and showed it with glee. "
        f"{helper.id} clapped softly, \"How neat! How grand!\" "
        f"and {mystery.label} was put back close at hand."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.topic]
    mystery_key = TOPIC_TO_MYSTERY.get(params.topic, "bell")
    mystery = MYSTERIES[mystery_key]
    world = World(setting, mystery)

    guest_cfg = GUESTS[params.guest]
    guest = world.add(Entity(
        id="Guest",
        kind="character",
        type=guest_cfg["type"],
        label=guest_cfg["label"],
        phrase=guest_cfg["phrase"],
        meters={"curiosity": 1.0, "joy": 0.5},
        memes={"wonder": 1.0, "care": 0.5},
    ))
    host = world.add(Entity(
        id="Host",
        kind="character",
        type="mother",
        label="the host",
        phrase="the kindly host",
        meters={"care": 1.0, "patience": 1.0},
        memes={"worry": 0.5},
    ))
    missing = world.add(Entity(
        id="Missing",
        kind="thing",
        type=mystery.id,
        label=mystery.label,
        phrase=mystery.label,
        owner=host.id,
        caretaker=host.id,
        meters={"hidden": 1.0},
        memes={"secret": 1.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        kind="thing",
        type=mystery.clue_kind,
        label=f"a little trail of {mystery.clue_kind}",
        phrase=f"a little trail of {mystery.clue_kind}",
        owner=missing.id,
        meters={"notice": 1.0},
    ))

    world.facts.update(guest=guest, host=host, missing=missing, clue=clue, mystery=mystery, setting=setting)

    world.say(rhyme_opening(guest, setting, mystery))
    world.say(f"\"Welcome,\" said {host.id}, with a smile soft and wide.")
    world.say(f"But {guest.id} looked around with a curious eye and a tiny surprise.")
    world.para()
    world.say(rhyme_conflict(guest, mystery, setting))
    world.say(f"The host felt the worry, yet kept the voice bright: \"Let's look for a clue in the warm, cozy light.\"")
    world.say(rhyme_clue(mystery))
    world.para()

    guest.memes["wonder"] += 1.0
    guest.meters["search"] = 1.0
    clue.meters["notice"] += 1.0
    missing.meters["hidden"] = 0.0
    missing.meters["found"] = 1.0

    world.say(rhyme_solution(guest, mystery, host))
    world.say(f"Then {mystery.label} was back where it belonged, and the room felt calm as a soft little song.")
    world.say(f"And that was the end of the riddle that day, with {guest.id} smiling and ready to play.")
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("topic", key))
    for key in GUESTS:
        lines.append(asp.fact("guest_kind", key))
    for key, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", key))
        lines.append(asp.fact("missing_kind", key, m.missing))
        lines.append(asp.fact("clue_kind", key, m.clue_kind))
    for topic, mystery in TOPIC_TO_MYSTERY.items():
        lines.append(asp.fact("maps_to", topic, mystery))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.

valid(T, G) :- topic(T), guest_kind(G), maps_to(T, M), mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a guest and a mystery to solve.")
    ap.add_argument("--topic", choices=sorted(SETTINGS), default=None)
    ap.add_argument("--guest", choices=sorted(GUESTS), default=None)
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
    topic = args.topic or rng.choice(sorted(SETTINGS))
    guest = args.guest or rng.choice(sorted(GUESTS))
    if topic not in SETTINGS:
        raise StoryError("Unknown topic.")
    if guest not in GUESTS:
        raise StoryError("Unknown guest.")
    return StoryParams(topic=topic, guest=guest)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short nursery-rhyme story about a {f['guest'].label} visiting {f['setting'].place} and solving a tiny mystery.",
        f"Tell a gentle rhyme where {f['guest'].id} notices that {f['mystery'].label} is missing and helps find it.",
        f"Make a child-friendly story with a guest, a clue, and a happy ending in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    guest = f["guest"]
    host = f["host"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who came to {setting.place} in the story?",
            answer=f"{guest.id} came to {setting.place} as the guest, and {host.id} welcomed {guest.pronoun('object')} there.",
        ),
        QAItem(
            question=f"What was the mystery in the nursery-rhyme story?",
            answer=f"The mystery was that {mystery.label} was {mystery.missing}. Everyone looked for the missing thing until it was found.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{guest.id} followed a clue with {mystery.clue_kind} and found {mystery.label} in {mystery.likely_hider}, then {host.id} put it back safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out a mystery.",
        ),
        QAItem(
            question="What does a guest do?",
            answer="A guest visits someone else's place and is welcomed there.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or hidden that people try to understand or solve.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    py = {(t, g) for t in SETTINGS for g in GUESTS}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(topic="topic", guest="rabbit"),
    StoryParams(topic="guest", guest="cat"),
    StoryParams(topic="song", guest="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible pairs:")
        for t, g in pairs:
            print(f"  {t} / {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
