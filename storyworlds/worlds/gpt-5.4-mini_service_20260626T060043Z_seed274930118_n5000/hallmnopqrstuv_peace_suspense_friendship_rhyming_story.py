#!/usr/bin/env python3
"""
Storyworld: hall, peace, suspense, friendship, rhyming story.

A small, self-contained classical simulation where two friends move through a
hall, sense a mystery, and restore peace together.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hall:
    name: str = "hallmnopqrstuv hall"
    echo: bool = True
    quiet: bool = False


@dataclass
class StoryParams:
    place: str
    mystery: str
    prize: str
    name: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, hall: Hall) -> None:
        self.hall = hall
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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

        clone = World(self.hall)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
HALLS = {
    "hallmnopqrstuv": Hall(name="hallmnopqrstuv hall", echo=True, quiet=False),
    "quiet hall": Hall(name="quiet hall", echo=False, quiet=True),
}

MYSTERIES = {
    "whisper": {
        "label": "a whisper",
        "verb": "hear a whisper",
        "rush": "tiptoe toward the sound",
        "sound": "soft and thin",
        "risk": "fear",
        "turn": "a lantern glow",
    },
    "shadow": {
        "label": "a shadow",
        "verb": "spot a shadow",
        "rush": "walk toward the dark shape",
        "sound": "long and light",
        "risk": "worry",
        "turn": "a brave smile",
    },
    "lostkey": {
        "label": "a lost key",
        "verb": "look for a lost key",
        "rush": "search by the door",
        "sound": "tinny and bright",
        "risk": "tension",
        "turn": "a careful helping hand",
    },
}

PRIZES = {
    "toy": {"label": "toy train", "phrase": "a little toy train", "place": "bench", "risk": "drop"},
    "book": {"label": "book", "phrase": "a picture book", "place": "table", "risk": "tear"},
    "bell": {"label": "bell", "phrase": "a shiny bell", "place": "shelf", "risk": "clatter"},
}

NAMES = ["Mia", "Noah", "Luna", "Eli", "Rose", "Theo", "Ava", "Finn"]
FRIENDS = ["friend", "pal", "buddy", "mate"]
OPENINGS = [
    "In hallmnopqrstuv hall, where echoes could hum,",
    "In a quiet little hall, where footsteps could drum,",
    "By the tall hall door, where shadows could come,",
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def predict_tension(world: World, mystery_id: str, prize_id: str) -> dict[str, bool]:
    sim = world.copy()
    return {
        "scary": mystery_id in {"whisper", "shadow"},
        "at_risk": prize_id in {"toy", "book", "bell"},
    }


def setup_story(world: World, hero: Entity, friend: Entity, mystery: dict, prize: dict) -> None:
    world.say(
        f"{random.choice(OPENINGS)} {hero.id} and {friend.id} came with a grin, "
        f"to share the hall and keep peace within."
    )
    world.say(
        f"{hero.id} loved the hall, with its long, bright floor, "
        f"and {friend.id} loved to wander and notice more."
    )
    world.para()
    world.say(
        f"Then {hero.id} saw {mystery['label']} near the wall, "
        f"{mystery['sound']} and strange in the quiet hall."
    )
    world.say(
        f"{friend.id} saw {prize['phrase']} tucked close by the door, "
        f"and both friends knew they should look for more."
    )


def build_conflict(world: World, hero: Entity, friend: Entity, mystery: dict, prize: dict) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    friend.memes["care"] = friend.memes.get("care", 0) + 1
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.say(
        f"{hero.id} wanted to {mystery['verb']}, though the air felt tight, "
        f"and {friend.id} held the {prize['label']} more snug and right."
    )
    world.say(
        f"\"Let's go slow,\" said {friend.id}, \"and stay side by side; "
        f"the hall can be spooky, but friendship is a guide.\""
    )
    if predict_tension(world, hero.id, prize["label"],)["scary"]:
        world.facts["suspense"] = True
        world.facts["risk"] = prize["risk"]


def resolve_story(world: World, hero: Entity, friend: Entity, mystery: dict, prize: dict) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    friend.memes["peace"] = friend.memes.get("peace", 0) + 1
    world.say(
        f"Together they searched, with gentle cheer, "
        f"and found that the sound was not trouble near."
    )
    world.say(
        f"It was just {mystery['turn']}, and the hall felt bright; "
        f"the shadow grew small in the warm lamp light."
    )
    world.para()
    world.say(
        f"{hero.id} and {friend.id} smiled, their shoulders at ease, "
        f"and the hall turned soft like a calm small breeze."
    )
    world.say(
        f"They set the {prize['label']} back where it should stay, "
        f"and peace came humming to end the day."
    )


def tell(params: StoryParams) -> World:
    hall = HALLS[params.place]
    mystery = MYSTERIES[params.mystery]
    prize = PRIZES[params.prize]
    world = World(hall)

    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type="child"))

    world.facts.update(hero=hero, friend=friend, mystery=mystery, prize=prize, hall=hall)
    setup_story(world, hero, friend, mystery, prize)
    build_conflict(world, hero, friend, mystery, prize)
    resolve_story(world, hero, friend, mystery, prize)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combo(place: str, mystery: str, prize: str) -> bool:
    return place in HALLS and mystery in MYSTERIES and prize in PRIZES


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in HALLS:
        for mystery in MYSTERIES:
            for prize in PRIZES:
                if valid_combo(place, mystery, prize):
                    out.append((place, mystery, prize))
    return out


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child about {f["hero"].id}, {f["friend"].id}, '
        f'and a mystery in {f["hall"].name}.',
        f'Tell a gentle suspense story where friendship helps calm the hall and bring peace.',
        f'Write a simple story with the word "{f["hall"].name}" and an ending that feels peaceful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mystery = f["mystery"]
    prize = f["prize"]
    qa = [
        QAItem(
            question=f"Who were the two friends in the hall?",
            answer=f"The two friends were {hero.id} and {friend.id}. They walked together in {f['hall'].name}.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful at first?",
            answer=f"It felt suspenseful when {hero.id} noticed {mystery['label']} and the hall grew quiet and still.",
        ),
        QAItem(
            question=f"What did the friends do to keep the {prize['label']} safe?",
            answer=f"They stayed side by side, moved carefully, and put the {prize['label']} back where it belonged.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the friends smiling in peace, after they learned the mystery was harmless.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is peace?",
            answer="Peace is a calm and friendly feeling when nobody is fighting and everyone can relax.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important or a little scary might happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_kind(M).
prize(X) :- prize_kind(X).

valid(P,M,X) :- place(P), mystery(M), prize(X).
peaceful_story(P,M,X) :- valid(P,M,X), calming_turn(M).
calming_turn(whisper).
calming_turn(shadow).
calming_turn(lostkey).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in HALLS:
        lines.append(asp.fact("setting", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_kind", m))
    for x in PRIZES:
        lines.append(asp.fact("prize_kind", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Hall, peace, suspense, friendship, rhyming story.")
    ap.add_argument("--place", choices=HALLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, prize = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, mystery=mystery, prize=prize, name=name, friend=friend)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
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
    StoryParams(place="hallmnopqrstuv", mystery="whisper", prize="toy", name="Mia", friend="Noah"),
    StoryParams(place="hallmnopqrstuv", mystery="shadow", prize="book", name="Luna", friend="Eli"),
    StoryParams(place="quiet hall", mystery="lostkey", prize="bell", name="Ava", friend="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
