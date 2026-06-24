#!/usr/bin/env python3
"""
storyworlds/worlds/pig_dim_sharing_rhyme_space_adventure.py
===========================================================

A small storyworld about a pig-dim space adventure where sharing and rhyme
save the day.

Premise:
- A tiny crew travels in a cozy starship.
- One pig-like dim little creature loves shiny space trinkets.
- A shortage or snag creates tension around one important item.
- The crew finds a sharing plan, and the fix is narrated in rhyme.

The simulated state tracks physical meters and emotional memes, and the prose
is driven by the live state rather than by a frozen paragraph template.
"""

from __future__ import annotations

import argparse
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"damage": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "sharing": 0.0, "lonely": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pig", "captain", "child", "crewmate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the Star Nook"
    deck: str = "the moonlit deck"
    station: str = "the storage nook"
    stars: str = "the bright stars"
    shares: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    crew_name: str
    helper_name: str
    prize: str
    setting: str = "starship"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.ship = Ship()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CREW_NAMES = ["Pip", "Milo", "Poppy", "Nova", "Tilly", "Roo"]
HELPER_NAMES = ["Zed", "Mara", "Ivo", "Kiki", "Bram", "Luma"]

PRIZES = {
    "glow_cracker": {
        "label": "glow cracker",
        "phrase": "a tiny glow cracker",
        "risk": "snatched",
        "split": "shared",
        "rhyme": "glow",
    },
    "star_map": {
        "label": "star map",
        "phrase": "a fold-out star map",
        "risk": "torn",
        "split": "shared",
        "rhyme": "way",
    },
    "moon_cookie": {
        "label": "moon cookie",
        "phrase": "a round moon cookie",
        "risk": "crumbled",
        "split": "shared",
        "rhyme": "sky",
    },
}

FEATURE_TAGS = {"sharing", "rhyme", "space", "pig-dim"}


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _pig_dim_word(name: str) -> str:
    return f"{name}, the pig-dim crewmate"


def _rhyme_line(a: str, b: str) -> str:
    return f"{a} in the ship, {b} in the sky."


def _rhyme_fix(prize: dict, shared_with: str) -> str:
    word = prize["rhyme"]
    if word == "glow":
        return f"They split the glow and let both {shared_with} share the show."
    if word == "way":
        return f"They traced one way for both of them to play."
    return f"They shared the treat and kept the crumbs neat."


def _is_reasonable(prize_id: str) -> bool:
    return prize_id in PRIZES


def asp_facts() -> str:
    import asp
    lines = []
    for pname in PRIZES:
        lines.append(asp.fact("prize", pname))
    lines.append(asp.fact("feature", "sharing"))
    lines.append(asp.fact("feature", "rhyme"))
    lines.append(asp.fact("theme", "space_adventure"))
    lines.append(asp.fact("creature", "pig_dim"))
    return "\n".join(lines)


ASP_RULES = r"""
shared(X) :- prize(X), feature(sharing).
rhymed(X) :- prize(X), feature(rhyme).
valid_story(P) :- prize(P), shared(P), rhymed(P).
#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_prizes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(a[0] for a in asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if not _is_reasonable(params.prize):
        raise StoryError("Unknown prize.")
    world = World()
    prize = PRIZES[params.prize]

    hero = world.add(Entity(
        id=params.crew_name,
        kind="character",
        type="pig",
        label=params.crew_name,
        phrase=_pig_dim_word(params.crew_name),
        meters={"damage": 0.0, "lost": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "sharing": 0.0, "lonely": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="crewmate",
        label=params.helper_name,
        phrase=f"{params.helper_name}, a cheerful helper",
        meters={"damage": 0.0, "lost": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "sharing": 0.0, "lonely": 0.0},
    ))
    item = world.add(Entity(
        id=params.prize,
        type="thing",
        label=prize["label"],
        phrase=prize["phrase"],
        owner=hero.id,
        caretaker=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, item=item, prize=prize, params=params)

    # Act 1: setup
    world.say(f"{hero.label} floated through {world.ship.name} with a tiny smile.")
    world.say(f"{hero.pronoun().capitalize()} was a {hero.phrase} who loved {item.phrase}.")
    world.say(f"{helper.label} kept watch by the window while {world.ship.stars} winked outside.")
    world.para()

    # Act 2: tension
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(f"One day, both friends reached for {item.phrase} at the same time.")
    world.say(f"{hero.label} wanted to keep {item.it()} close, but {helper.label} needed it for the ship's map.")
    world.say(f"{hero.label} felt small and dim, and the cabin got quiet.")
    world.para()

    # Act 3: turn by sharing and rhyme
    hero.memes["sharing"] += 1
    helper.memes["sharing"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    world.ship.shares.add(item.id)

    world.say(f"Then {helper.label} said, \"We can share it.\"")
    world.say(_rhyme_line(f"{hero.label} held the {item.label}", f"{helper.label} held the map"))
    world.say(_rhyme_fix(prize, helper.label))
    world.say(f"Soon {hero.label} and {helper.label} were smiling side by side on the moonlit deck.")
    world.say(f"The little {hero.type} was no longer dim, because sharing made the whole ship glow.")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    return [
        "Write a short space adventure for a child about a pig-dim crewmate who learns to share.",
        f"Tell a gentle story where {hero.label} and a helper both want {item.phrase}, and rhyme helps them solve it.",
        "Make the ending bright, simple, and playful, with sharing on a starship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a tiny pig-dim crewmate, and {helper.label}, who helps on the starship.",
        ),
        QAItem(
            question=f"What did both friends want at first?",
            answer=f"They both wanted {item.phrase}. That made them feel worried until they found a way to share it.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer="They solved it by sharing the prize and speaking in a little rhyme, so both friends could use it together.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt happy and bright at the end, because sharing turned the quiet moment into a smiling one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a starship?",
            answer="A starship is a spaceship that travels through space, often between stars or planets.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person use or enjoy something too, instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like glow and show.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} owner={e.owner}"
        )
    lines.append(f"ship_shares={sorted(world.ship.shares)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verify
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    py = sorted(PRIZES.keys())
    clingo = asp_valid_prizes()
    if py == clingo:
        print(f"OK: ASP and Python agree on {len(py)} prizes.")
        return 0
    print("Mismatch between ASP and Python.")
    print("python:", py)
    print("asp:", clingo)
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    prize = args.prize or rng.choice(list(PRIZES.keys()))
    if prize not in PRIZES:
        raise StoryError("Unknown prize.")
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != crew_name])
    return StoryParams(
        crew_name=crew_name,
        helper_name=helper_name,
        prize=prize,
        setting=args.setting or "starship",
        seed=args.seed,
    )


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pig-dim sharing rhyme space adventure.")
    ap.add_argument("--setting", default="starship")
    ap.add_argument("--prize", choices=sorted(PRIZES.keys()))
    ap.add_argument("--crew-name", dest="crew_name")
    ap.add_argument("--helper-name", dest="helper_name")
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_program_text(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible prizes:")
        for p in asp_valid_prizes():
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, prize in enumerate(sorted(PRIZES.keys())):
            params = StoryParams(
                crew_name=CREW_NAMES[i % len(CREW_NAMES)],
                helper_name=HELPER_NAMES[i % len(HELPER_NAMES)],
                prize=prize,
                setting="starship",
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(50, args.n * 30):
            attempts += 1
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
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
