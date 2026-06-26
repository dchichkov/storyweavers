#!/usr/bin/env python3
"""
A cozy bedtime story world: a child hears muttering in the apartment courtyard,
finds small clues, and solves a gentle mystery with a kind ending image.

The simulated domain is intentionally tiny:
- setting: apartment courtyard
- mystery: a soft, child-sized puzzle about a missing object
- foreshadowing: clues appear before the reveal
- emotional state: worry, curiosity, relief, warmth

The story is driven by world state rather than a frozen paragraph.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Courtyard:
    name: str = "the apartment courtyard"
    details: list[str] = field(default_factory=list)
    clues: list[str] = field(default_factory=list)


class World:
    def __init__(self, courtyard: Courtyard) -> None:
        self.courtyard = courtyard
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    mystery: str
    clue_style: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mina", "Luna", "Ada", "Nora", "Ivy", "Maya"],
    "boy": ["Noah", "Eli", "Theo", "Finn", "Ben", "Leo"],
}
PARENTS = ["mother", "father"]
TRAITS = ["sleepy", "curious", "gentle", "quiet"]
MYSTERIES = {
    "lost_key": {
        "label": "a small brass key",
        "phrase": "a small brass key for the mailbox",
        "missing_where": "near the flower pots",
        "reveal": "it had slipped under the doormat by the courtyard door",
        "effect": "opened the little mailbox",
    },
    "missing_cat": {
        "label": "the gray cat",
        "phrase": "the sleepy gray cat from the first floor",
        "missing_where": "behind the bench",
        "reveal": "the gray cat was napping inside the laundry basket",
        "effect": "purred softly and blinked awake",
    },
    "rattling_windchime": {
        "label": "the wind chime",
        "phrase": "a tiny silver wind chime",
        "missing_where": "by the stair rail",
        "reveal": "it had blown into the ivy and was tapping there",
        "effect": "made the courtyard sing again",
    },
}
CLUES = [
    "a soft mutter from the stairwell",
    "a line of tiny footprints in the dust",
    "a faint jingle near the planters",
    "a cat-shaped shadow by the bench",
    "a shiny glint under the leaves",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cozy apartment-courtyard mystery story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--clue-style", choices=["soft", "sparkly", "tiny"], dest="clue_style")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    clue_style = args.clue_style or rng.choice(["soft", "sparkly", "tiny"])
    return StoryParams(name=name, gender=gender, parent=parent, mystery=mystery, clue_style=clue_style)


def _add_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + value


def tell(params: StoryParams) -> World:
    courtyard = Courtyard()
    world = World(courtyard)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "sleepy"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    mystery = MYSTERIES[params.mystery]
    object_ent = world.add(Entity(
        id="mystery_object",
        kind="thing",
        type="object",
        label=mystery["label"],
        phrase=mystery["phrase"],
        owner="courtyard",
    ))

    clue1, clue2 = CLUES[0], CLUES[1]
    if params.clue_style == "sparkly":
        clue1, clue2 = CLUES[2], CLUES[4]
    elif params.clue_style == "tiny":
        clue1, clue2 = CLUES[1], CLUES[3]

    world.say(f"{hero.id} was a little {params.gender} who liked bedtime stories and warm quiet nights.")
    world.say(f"{hero.id} loved sitting in {world.courtyard.name} with {hero.pronoun('possessive')} {params.parent}.")
    world.say(f"One night, there was a tiny mystery to solve: {mystery['phrase']} was missing.")

    world.para()
    _add_meter(hero, "curiosity", 1)
    _add_meter(hero, "worry", 1)
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} heard a soft mutter and peeked toward the courtyard steps.")
    world.say(f"There was {clue1}, which felt like a clue, and {clue2}, which felt like another clue.")
    world.say(f"{hero.id} whispered, 'I think something is trying to tell me where to look.'")

    world.para()
    _add_meter(hero, "search", 1)
    world.say(f"{hero.id} tiptoed past the flower pots and looked {mystery['missing_where']}.")
    world.say(f"{hero.pronoun().capitalize()} checked the bench, the ivy, and the little mailboxes.")
    world.say(f"The muttering turned into a gentle rustle, and then the answer came into view.")
    world.say(f"It was true: {mystery['reveal']}.")

    world.para()
    _add_meter(hero, "relief", 1)
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(f"{hero.id} smiled and called to {hero.pronoun('possessive')} {params.parent}, 'I found it!'")
    world.say(f"The little mystery was solved, and {mystery['effect']}.")
    world.say(f"{hero.id} felt cozy and proud as the courtyard grew still again, like a blanket tucked over the night.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "object": object_ent,
        "mystery": params.mystery,
        "clue_style": params.clue_style,
        "courtyard": courtyard,
        "reveal": mystery["reveal"],
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    obj = f["object"]
    return [
        f"Write a bedtime story about {hero.id} hearing a mutter in {world.courtyard.name} and solving a small mystery.",
        f"Tell a gentle story where {hero.id} and {parent.label} look for {obj.phrase} in the apartment courtyard.",
        f"Write a cozy mystery for a young child that begins with a quiet clue and ends with relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    obj = f["object"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} need to solve in {world.courtyard.name}?",
            answer=f"{hero.id} needed to find {obj.phrase}. The missing thing was the little mystery at the center of the story.",
        ),
        QAItem(
            question=f"What clue first made {hero.id} look more closely in the courtyard?",
            answer=f"{hero.id} heard a soft mutter and noticed small clues nearby, which made {hero.pronoun('object')} curious instead of scared.",
        ),
        QAItem(
            question=f"How did the story end after {hero.id} solved the mystery?",
            answer=f"The story ended with {hero.id} finding the missing thing and feeling cozy, proud, and ready for sleep beside {hero.pronoun('possessive')} {parent.type}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a courtyard?",
            answer="A courtyard is an open shared space inside or beside a building, often with paths, plants, benches, and doors around it.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to use clues and careful looking to figure out what happened or where something is.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives small hints before the important answer is revealed later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "apartment_courtyard"),
            asp.fact("feature", "mystery_to_solve"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("style", "bedtime_story"),
            asp.fact("word", "mutter"),
        ]
    )


ASP_RULES = r"""
setting(apartment_courtyard).
feature(mystery_to_solve).
feature(foreshadowing).
style(bedtime_story).
keyword(mutter).
valid_story :- setting(apartment_courtyard), feature(mystery_to_solve), feature(foreshadowing), style(bedtime_story), keyword(mutter).
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(getattr(sym, "name", "") == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin validates the storyworld premise.")
        return 0
    print("MISMATCH: ASP twin did not validate the storyworld premise.")
    return 1


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mina", gender="girl", parent="mother", mystery="lost_key", clue_style="soft"),
            StoryParams(name="Leo", gender="boy", parent="father", mystery="missing_cat", clue_style="sparkly"),
            StoryParams(name="Nora", gender="girl", parent="mother", mystery="rattling_windchime", clue_style="tiny"),
        ]
        for p in curated:
            samples.append(generate(p))
        return samples

    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/0."))
        return

    samples = build_samples(args)

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
