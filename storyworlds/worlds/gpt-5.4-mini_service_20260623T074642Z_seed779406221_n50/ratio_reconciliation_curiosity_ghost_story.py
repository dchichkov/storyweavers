#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/ratio_reconciliation_curiosity_ghost_story.py
===============================================================================================================

A small standalone storyworld in a ghost-story style.

Seed-inspired premise:
- A curious child finds a ghostly ratio carved into an old attic beam.
- The ratio is important because it keeps two haunted things in balance.
- A misunderstanding breaks the balance, the ghost grows lonely, and the child
  must use curiosity to uncover the true meaning.
- Reconciliation arrives when the child sets the balance right and makes peace
  with the ghost.

The world is intentionally small and classical:
- one setting
- one curious hero
- one ghostly companion
- one ratio-based constraint
- one emotional arc: curiosity -> tension -> reconciliation

It supports the Storyweavers contract: generate, emit, parser, QA, trace, ASP,
and verification.
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
# Domain entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    echoes: bool = True


@dataclass
class RatioPuzzle:
    left_name: str
    right_name: str
    left_count: int
    right_count: int
    desired_left: int
    desired_right: int
    clue: str


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    caretaker_type: str
    puzzle: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty"),
    "churchyard": Setting(place="the churchyard", mood="quiet"),
    "hall": Setting(place="the old hall", mood="echoing"),
}

PUZZLES = {
    "candles": RatioPuzzle(
        left_name="blue candles",
        right_name="white candles",
        left_count=2,
        right_count=3,
        desired_left=4,
        desired_right=6,
        clue="the ghost wanted the candles lit in the same ratio as before",
    ),
    "windows": RatioPuzzle(
        left_name="open windows",
        right_name="shut windows",
        left_count=1,
        right_count=2,
        desired_left=2,
        desired_right=4,
        clue="the draft only calmed down when the windows matched the old ratio",
    ),
    "bells": RatioPuzzle(
        left_name="small bells",
        right_name="large bells",
        left_count=3,
        right_count=1,
        desired_left=6,
        desired_right=2,
        clue="the bells had to ring in the same pattern as the ghost's memory",
    ),
}

HERO_NAMES = ["Mina", "Nora", "Ivy", "Mabel", "Lena", "Elsie"]
CARETAKERS = {"mother": "mother", "father": "father", "grandmother": "grandmother", "grandfather": "grandfather"}


# ---------------------------------------------------------------------------
# World model and story logic
# ---------------------------------------------------------------------------
def describe_setting(setting: Setting) -> str:
    return {
        "attic": "The attic was dusty and dim, with beams that sighed in the dark.",
        "churchyard": "The churchyard was quiet, with pale stones and a cold little wind.",
        "hall": "The old hall felt like it was holding its breath.",
    }[next(k for k, v in SETTINGS.items() if v.place == setting.place)]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    puzzle = PUZZLES[params.puzzle]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker_type, label=params.caretaker_type))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))
    world.add(Entity(
        id="Puzzle",
        kind="thing",
        type="puzzle",
        label="ratio puzzle",
        owner=ghost.id,
        props={
            "left_name": puzzle.left_name,
            "right_name": puzzle.right_name,
            "left_count": str(puzzle.left_count),
            "right_count": str(puzzle.right_count),
            "desired_left": str(puzzle.desired_left),
            "desired_right": str(puzzle.desired_right),
        },
    ))
    world.facts.update(hero=hero, caretaker=caretaker, ghost=ghost, puzzle=puzzle)
    return world


def intro(world: World) -> None:
    hero = world.facts["hero"]
    world.say(
        f"{hero.id} was a little {hero.type} who liked quiet places because quiet places let curiosity speak softly."
    )
    world.say(describe_setting(world.setting))
    world.say("One night, a pale glow flickered near a beam, as if something hidden wanted to be found.")


def curiosity_turn(world: World) -> None:
    hero = world.facts["hero"]
    puzzle: RatioPuzzle = world.facts["puzzle"]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} followed the glow and found {puzzle.clue}. "
        f"On the beam, someone had scratched a ratio: {puzzle.left_count}:{puzzle.right_count}."
    )
    world.say(
        f"{hero.id} wondered why the numbers mattered, so {hero.pronoun().capitalize()} counted the little shapes by hand."
    )


def tension(world: World) -> None:
    hero = world.facts["hero"]
    caretaker = world.facts["caretaker"]
    ghost = world.facts["ghost"]
    puzzle: RatioPuzzle = world.facts["puzzle"]
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    ghost.memes["lonely"] = ghost.memes.get("lonely", 0) + 1
    world.say(
        f"{hero.id} first guessed the answer wrong and moved the pieces into a crooked line."
    )
    world.say(
        f"The ghost drifted colder, because the old pattern was broken and the room felt uneven."
    )
    world.say(
        f"{caretaker.label.capitalize()} heard the rattling and came closer, but {hero.id} kept staring at the numbers."
    )
    world.facts["broken_ratio"] = f"{puzzle.left_count}:{puzzle.right_count}"


def reconcile(world: World) -> None:
    hero = world.facts["hero"]
    caretaker = world.facts["caretaker"]
    ghost = world.facts["ghost"]
    puzzle: RatioPuzzle = world.facts["puzzle"]
    world.say(
        f"{hero.id} tried again, this time counting carefully: if there were {puzzle.left_count} on one side, there must be {puzzle.right_count} on the other."
    )
    world.say(
        f"Then {hero.id} set the pieces into the right ratio, {puzzle.desired_left}:{puzzle.desired_right}, and the strange cold began to loosen."
    )
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    ghost.memes["lonely"] = 0
    ghost.memes["peace"] = ghost.memes.get("peace", 0) + 1
    world.say(
        f"The ghost smiled like moonlight on glass. It had never wanted a scare at all; it only wanted someone kind enough to notice the pattern."
    )
    world.say(
        f"{hero.id} smiled back, and {caretaker.label} put an arm around {hero.pronoun('object')}. "
        f"Together they left the room brighter than they found it."
    )
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    world.para()
    curiosity_turn(world)
    world.para()
    tension(world)
    world.para()
    reconcile(world)
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    puzzle: RatioPuzzle = world.facts["puzzle"]
    return [
        f"Write a gentle ghost story for children about {hero.id} discovering a secret ratio in {world.setting.place}.",
        f"Tell a short story where curiosity helps {hero.id} solve a {puzzle.left_count}:{puzzle.right_count} pattern and make peace with a ghost.",
        "Write a spooky-but-kind story that ends with reconciliation after a child fixes a broken balance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    caretaker = world.facts["caretaker"]
    ghost = world.facts["ghost"]
    puzzle: RatioPuzzle = world.facts["puzzle"]
    return [
        QAItem(
            question=f"Who found the glowing ratio in {world.setting.place}?",
            answer=f"{hero.id} found it, while the ghost stayed nearby in the dark room.",
        ),
        QAItem(
            question="What number pattern did the beam show?",
            answer=f"It showed the ratio {puzzle.left_count}:{puzzle.right_count}.",
        ),
        QAItem(
            question=f"Why did the ghost feel better at the end?",
            answer=f"The ghost felt better because {hero.id} fixed the ratio and understood the pattern instead of fearing it.",
        ),
        QAItem(
            question=f"Who stayed with {hero.id} after the scare?",
            answer=f"{caretaker.label.capitalize()} stayed with {hero.id}, and they left the room together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ratio?",
            answer="A ratio is a way to compare two amounts and show how much of one thing there is compared with another.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, so you look, ask, and think about what is happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after a disagreement or misunderstanding.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.

setting(attic).
setting(churchyard).
setting(hall).

puzzle(candles).
puzzle(windows).
puzzle(bells).

valid_story(S,P,H) :- setting(S), puzzle(P), hero(H).
hero(mina).
hero(nora).
hero(ivy).
hero(mabel).
hero(lena).
hero(elsie).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PUZZLES:
        lines.append(asp.fact("puzzle", pid))
    for h in ["mina", "nora", "ivy", "mabel", "lena", "elsie"]:
        lines.append(asp.fact("hero", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(s, p, h) for s in SETTINGS for p in PUZZLES for h in ["mina", "nora", "ivy", "mabel", "lena", "elsie"]}
    got = set(asp_valid_stories())
    if expected == got:
        print(f"OK: ASP and Python agree on {len(got)} simple story triples.")
        return 0
    print("MISMATCH between ASP and Python story triples.")
    print(" only in ASP:", sorted(got - expected))
    print(" only in Python:", sorted(expected - got))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness / resolution
# ---------------------------------------------------------------------------
def explain_invalid(params: StoryParams) -> str:
    return "Invalid story request: this ghost story only accepts known settings and puzzle types."


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    puzzle = args.puzzle or rng.choice(list(PUZZLES))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or "girl"
    caretaker_type = args.caretaker_type or "mother"
    if setting not in SETTINGS or puzzle not in PUZZLES:
        raise StoryError(explain_invalid(StoryParams(setting, name, hero_type, caretaker_type, puzzle)))
    return StoryParams(
        setting=setting,
        hero_name=name,
        hero_type=hero_type,
        caretaker_type=caretaker_type,
        puzzle=puzzle,
        seed=args.seed,
    )


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  setting: {world.setting.place}")
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="attic", hero_name="Mina", hero_type="girl", caretaker_type="mother", puzzle="candles"),
    StoryParams(setting="churchyard", hero_name="Ivy", hero_type="girl", caretaker_type="grandmother", puzzle="windows"),
    StoryParams(setting="hall", hero_name="Nora", hero_type="girl", caretaker_type="father", puzzle="bells"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about curiosity, ratio, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--puzzle", choices=PUZZLES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--caretaker-type", choices=list(CARETAKERS))
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        for triple in sorted(set(asp.atoms(model, "valid_story"))):
            print(triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.puzzle}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
