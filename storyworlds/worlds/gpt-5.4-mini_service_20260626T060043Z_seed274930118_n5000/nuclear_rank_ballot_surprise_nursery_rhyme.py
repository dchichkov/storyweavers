#!/usr/bin/env python3
"""
Storyworld: a nursery-rhyme ballot surprise.

A tiny, self-contained simulation about a small election in a cozy setting.
The child-friendly story has a clear setup, a gentle surprise, and a tidy
ending that changes the world state.

Core premise:
- Little characters sort toy tokens by rank.
- A ballot box decides who gets the star ribbon.
- One unexpected "nuclear" toy prank causes a surprise, but it is harmless and
  resolved through a calm, kind fix.

The story reads in a rhyming, sing-song style while remaining state-driven.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
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
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    indoors: bool = True


@dataclass
class Candidate:
    id: str
    label: str
    rank: int
    rhyme: str
    sparkle: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    rival: str
    surprise: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.rank_order: list[str] = []
        self.ballot: dict[str, int] = {}
        self.surprise_name: str = ""

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.rank_order = list(self.rank_order)
        c.ballot = dict(self.ballot)
        c.surprise_name = self.surprise_name
        return c


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True),
    "playroom": Setting(place="the playroom", indoors=True),
    "garden": Setting(place="the garden", indoors=False),
}

HEROES = [
    ("Milo", "boy"),
    ("Luna", "girl"),
    ("Tess", "girl"),
    ("Ollie", "boy"),
    ("Nia", "girl"),
]

RIVALS = [
    ("Pip", "boy"),
    ("Poppy", "girl"),
    ("Finn", "boy"),
    ("Ivy", "girl"),
]

SURPRISES = {
    "drum": "a tiny drum with a silver rim",
    "crown": "a paper crown with shiny dots",
    "kite": "a bright kite tied with string",
    "ribbon": "a red ribbon wrapped in a loop",
}

CANDIDATES = {
    "sun": Candidate("sun", "Sun", 3, "shine", "gold"),
    "moon": Candidate("moon", "Moon", 2, "glow", "pearl"),
    "star": Candidate("star", "Star", 1, "twinkle", "sparkle"),
}

# A harmless "nuclear" toy is a class-project word token, not a dangerous object.
NUCLEAR_TOKEN = "nuclear"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entity(name: str, gender: str, kind: str = "character") -> Entity:
    return Entity(id=name, kind=kind, type=gender, label=name)


def rhyming_intro(hero: Entity, setting: Setting) -> str:
    return (
        f"In {setting.place}, all tidy and neat, {hero.id} tapped a toe to a nursery beat."
    )


def rhyming_ballot_line() -> str:
    return "A ballot box sat on a little low stand, for choosing the rank with a careful hand."


def rank_sentence(candidate: Candidate) -> str:
    return f"{candidate.label} wore rank {candidate.rank}, and sparkled with {candidate.sparkle} light."


def surprise_line(surprise: str) -> str:
    return f"Then out came {SURPRISES[surprise]}, and everyone blinked in surprise."


def end_image(hero: Entity, winner: Candidate, surprise: str) -> str:
    return (
        f"So {hero.id} smiled at the ballot, and {winner.label} won the day; "
        f"the {surprise} stayed near the shelf, and the room felt snug and gay."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")

    setting = SETTINGS[params.setting]
    world = World(setting)
    world.surprise_name = params.surprise

    hero_name, hero_gender = next((n, g) for n, g in HEROES if n == params.hero)
    rival_name, rival_gender = next((n, g) for n, g in RIVALS if n == params.rival)
    hero = world.add(make_entity(hero_name, hero_gender))
    rival = world.add(make_entity(rival_name, rival_gender))
    ballot = world.add(Entity(id="ballot", kind="thing", type="box", label="ballot box"))
    token = world.add(Entity(id="token", kind="thing", type="token", label=NUCLEAR_TOKEN))

    world.rank_order = ["sun", "moon", "star"]
    world.ballot = {"sun": 0, "moon": 0, "star": 0}

    # Act 1: setup.
    world.say(rhyming_intro(hero, setting))
    world.say(f"{hero.id} and {rival.id} lined up to play a rank-by-rank game.")
    world.say("They had three bright cards to choose from: Sun, Moon, and Star.")
    world.say(rhyming_ballot_line())

    # Act 2: tension.
    world.para()
    world.say(
        f"{hero.id} liked the Star card best, because its rank was small and its twinkle was grand."
    )
    world.say(
        f"{rival.id} liked the Sun card best, because it felt warm and strong in hand."
    )
    world.say(
        f"Then the teacher set down a tiny class token marked {NUCLEAR_TOKEN}, just for a rhyme."
    )
    world.say(
        f"It was only a paper word, but it made a great surprise for the counting time."
    )
    world.say(surprise_line(params.surprise))
    token.meters["surprise"] = 1
    hero.memes["startle"] = 1
    rival.memes["startle"] = 1

    # Ballot action.
    world.say(
        f"{hero.id} dropped one ballot in, and {rival.id} dropped one in too; "
        f"the box went thumpity-thump, as little boxes do."
    )
    world.ballot["star"] += 2
    world.ballot["sun"] += 1
    world.ballot["moon"] += 1

    # Turn: surprise causes a pause, then a kind choice.
    world.para()
    world.say(
        f"The surprise made them laugh, and the laugh made the tension small."
    )
    world.say(
        f"{hero.id} said, 'Let's rank the cards by kindness, so everybody feels tall.'"
    )
    world.say(
        f"{rival.id} nodded, and the ballot stayed neat in its place."
    )

    # Resolution.
    winner = CANDIDATES["star"]
    winner_rank_before = winner.rank
    winner.rank = 1
    CANDIDATES["sun"].rank = 2
    CANDIDATES["moon"].rank = 3

    hero.memes["joy"] = 1
    rival.memes["joy"] = 1
    token.meters["surprise"] = 0  # the surprise is acknowledged and settled
    ballot.meters["used"] = 1
    world.facts.update(
        hero=hero,
        rival=rival,
        ballot=ballot,
        token=token,
        winner=winner,
        winner_rank_before=winner_rank_before,
    )

    world.say(
        f"The star card won the rank, and the others took their place in line."
    )
    world.say(
        f"{hero.id} and {rival.id} clapped together, and the whole room felt fine."
    )
    world.say(end_image(hero, winner, params.surprise))
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    winner: Candidate = f["winner"]
    surprise = world.surprise_name
    return [
        f"Write a short nursery-rhyme story in {world.setting.place} where {hero.id} and {rival.id} use a ballot to pick rank, and a {surprise} causes a surprise.",
        f"Tell a gentle rhyming tale about a ballot box, a rank of Sun Moon Star, and how {winner.label} wins kindly at the end.",
        f"Make a child-friendly story with the words nuclear, rank, ballot, and surprise, set in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    winner: Candidate = f["winner"]
    return [
        QAItem(
            question=f"Who used the ballot box in {world.setting.place}?",
            answer=f"{hero.id} and {rival.id} used the ballot box together.",
        ),
        QAItem(
            question="Which card won the highest rank in the story?",
            answer=f"{winner.label} won the highest rank after the ballot was counted.",
        ),
        QAItem(
            question="What made everybody pause and smile?",
            answer=f"The little {world.surprise_name} surprise made everybody pause and smile.",
        ),
        QAItem(
            question="Was the nuclear token dangerous in this story?",
            answer="No, it was only a paper class token with the word nuclear on it, so it was harmless.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ballot?",
            answer="A ballot is a slip or choice used for voting.",
        ),
        QAItem(
            question="What does rank mean?",
            answer="Rank means order, like first, second, or third.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people look up, laugh, or gasp.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(nursery).
setting(playroom).
setting(garden).

candidate(sun).
candidate(moon).
candidate(star).

rank(sun,3).
rank(moon,2).
rank(star,1).

ballot_choice(sun).
ballot_choice(moon).
ballot_choice(star).

winner(C) :- rank(C,1).

surprise_word(nuclear).
surprise_word(rank).
surprise_word(ballot).
surprise_word(surprise).

compatible_story(S) :- setting(S), surprise_word(nuclear), surprise_word(rank), surprise_word(ballot), surprise_word(surprise).
#show compatible_story/1.
#show winner/1.
"""


def asp_facts() -> str:
    import asp  # lazy import
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, cand in CANDIDATES.items():
        lines.append(asp.fact("candidate", cid))
        lines.append(asp.fact("rank", cid, cand.rank))
    lines.append(asp.fact("surprise_word", "nuclear"))
    lines.append(asp.fact("surprise_word", "rank"))
    lines.append(asp.fact("surprise_word", "ballot"))
    lines.append(asp.fact("surprise_word", "surprise"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp  # lazy import
    model = asp.one_model(asp_program("#show winner/1.\n#show compatible_story/1."))
    winners = set(asp.atoms(model, "winner"))
    compat = set(asp.atoms(model, "compatible_story"))
    ok = winners == {("star",)} and compat == {("nursery",), ("playroom",), ("garden",)}
    if ok:
        print("OK: ASP twin matches the Python world.")
        return 0
    print("Mismatch in ASP verification.")
    print("winner:", sorted(winners))
    print("compatible_story:", sorted(compat))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme ballot surprise storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=[n for n, _ in HEROES])
    ap.add_argument("--rival", choices=[n for n, _ in RIVALS])
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([n for n, _ in HEROES])
    rival = args.rival or rng.choice([n for n, _ in RIVALS if n != hero])
    surprise = args.surprise or rng.choice(list(SURPRISES))
    if hero == rival:
        raise StoryError("Hero and rival must be different characters.")
    return StoryParams(setting=setting, hero=hero, rival=rival, surprise=surprise, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = run_world(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
    lines.append(f"rank_order={world.rank_order}")
    lines.append(f"ballot={world.ballot}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show winner/1.\n#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp  # lazy import
        model = asp.one_model(asp_program("#show compatible_story/1.\n#show winner/1."))
        print("winner:", sorted(set(asp.atoms(model, "winner"))))
        print("compatible_story:", sorted(set(asp.atoms(model, "compatible_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="nursery", hero="Milo", rival="Poppy", surprise="drum"),
            StoryParams(setting="playroom", hero="Luna", rival="Finn", surprise="crown"),
            StoryParams(setting="garden", hero="Tess", rival="Ivy", surprise="kite"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
