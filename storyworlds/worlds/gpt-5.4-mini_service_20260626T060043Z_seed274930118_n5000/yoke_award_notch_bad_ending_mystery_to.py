#!/usr/bin/env python3
"""
A standalone storyworld about a small mystery in a warm family barnyard.

Theme seed words: yoke, award, notch
Style: heartwarming
Features: mystery to solve, bad-ending tension

Premise:
A child notices a cherished yoke has a tiny notch missing, and an award ribbon
from the barn fair has gone missing too. The family worries the day will end in
tears unless the child can solve the mystery in time.

The simulation models:
- physical meters: damaged, hidden, carried, hung, fixed, muddy
- emotional memes: worry, hope, pride, comfort, relief

The story variants are constrained: the evidence must actually fit the mystery,
and the repair must truly change the end state.
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
# Core domain objects
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hung_on: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    kind: str = "barnyard"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    points_to: str  # entity id it reveals


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    parent_type: str
    sibling_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------

class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_clue(self, c: Clue) -> Clue:
        self.clues[c.id] = c
        return c

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
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "barn": Place(id="barn", label="the red barn"),
    "yard": Place(id="yard", label="the back yard"),
    "stable": Place(id="stable", label="the little stable"),
}

HERO_NAMES = ["Maya", "Lina", "Sofi", "June", "Nora", "Ella", "Ivy"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Owen", "Sam", "Max", "Eli"]

AWARDS = {
    "blue_ribbon": {
        "label": "blue ribbon",
        "phrase": "a bright blue ribbon from the fair",
        "kind": "award",
    },
    "gold_medal": {
        "label": "gold medal",
        "phrase": "a shiny gold medal on a string",
        "kind": "award",
    },
    "little_trophy": {
        "label": "little trophy",
        "phrase": "a tiny trophy with a star on top",
        "kind": "award",
    },
}

YOKES = {
    "wood_yoke": {
        "label": "wooden yoke",
        "phrase": "a smooth wooden yoke",
        "kind": "yoke",
    },
    "painted_yoke": {
        "label": "painted yoke",
        "phrase": "a painted yoke with a little flower",
        "kind": "yoke",
    },
}

NOTCHES = {
    "round_notch": {
        "label": "round notch",
        "phrase": "a round notch carved into the side",
    },
    "tiny_notch": {
        "label": "tiny notch",
        "phrase": "a tiny notch near the middle",
    },
}

TRAITS = ["curious", "gentle", "brave", "cheerful", "patient", "kind"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def make_story_params(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    if place not in PLACES:
        raise StoryError("Unknown place.")
    name = args.name or rng.choice(HERO_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in HERO_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    sibling = args.sibling or rng.choice(["sister", "brother"])
    return StoryParams(place=place, hero_name=name, hero_gender=gender, parent_type=parent, sibling_type=sibling)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        traits=["little", rng_trait(params.hero_name)],
        meters={"hope": 0.0},
        memes={"worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        meters={"work": 0.0},
        memes={"worry": 0.0, "comfort": 0.0},
    ))
    sibling = world.add(Entity(
        id="sibling",
        kind="character",
        type=params.sibling_type,
        label=f"the {params.sibling_type}",
        memes={"worry": 0.0, "hope": 0.0},
    ))

    award_id = "award"
    yoke_id = "yoke"
    notch_id = "notch"

    award_cfg = random_choice_dict(AWARDS, params.hero_name)
    yoke_cfg = random_choice_dict(YOKES, params.hero_name)
    notch_cfg = random_choice_dict(NOTCHES, params.hero_name)

    award = world.add(Entity(
        id=award_id,
        type=award_cfg["kind"],
        label=award_cfg["label"],
        phrase=award_cfg["phrase"],
        owner=parent.id,
        hung_on="peg",
        meters={"hidden": 0.0, "found": 0.0},
    ))
    yoke = world.add(Entity(
        id=yoke_id,
        type=yoke_cfg["kind"],
        label=yoke_cfg["label"],
        phrase=yoke_cfg["phrase"],
        owner=parent.id,
        caretaker=parent.id,
        meters={"damaged": 0.0, "fixed": 0.0, "muddy": 0.0},
        memes={"pride": 0.0},
    ))
    notch = world.add(Entity(
        id=notch_id,
        type="mark",
        label=notch_cfg["label"],
        phrase=notch_cfg["phrase"],
        owner=yoke.id,
        meters={"seen": 0.0},
    ))

    clue = world.add_clue(Clue(
        id="clue1",
        label="sawdust trail",
        phrase="a little trail of sawdust leading under the bench",
        location="under the bench",
        points_to=award.id,
    ))

    world.facts.update(
        hero=hero, parent=parent, sibling=sibling, award=award, yoke=yoke,
        notch=notch, clue=clue, place=world.place, award_cfg=award_cfg,
        yoke_cfg=yoke_cfg, notch_cfg=notch_cfg
    )

    # Initial state: the award is missing and the yoke has a suspicious notch.
    award.meters["hidden"] = 1.0
    yoke.meters["damaged"] = 1.0
    hero.memes["worry"] += 1.0
    parent.memes["worry"] += 1.0
    sibling.memes["hope"] += 1.0

    return world


def rng_trait(name: str) -> str:
    return TRAITS[sum(ord(c) for c in name) % len(TRAITS)]


def random_choice_dict(d: dict, key: str) -> dict:
    keys = sorted(d)
    idx = sum(ord(c) for c in key) % len(keys)
    return d[keys[idx]]


def intro(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    yoke = world.facts["yoke"]
    award = world.facts["award"]

    world.say(
        f"{hero.id} was a little {hero.traits[1]} {hero.type} who loved helping at {world.place.label}."
    )
    world.say(
        f"{hero.id}'s {parent.type} was proud of {hero.id} and kept {award.phrase} in a safe place."
    )
    world.say(
        f"There was also {yoke.phrase} by the barn wall, and one side had {world.facts['notch'].phrase}."
    )


def build_conflict(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    sibling = world.facts["sibling"]
    award = world.facts["award"]
    yoke = world.facts["yoke"]
    clue = world.facts["clue"]

    hero.memes["worry"] += 1.0
    parent.memes["worry"] += 1.0

    world.para()
    world.say(
        f"One afternoon, {hero.id} noticed the {award.label} was gone from its peg."
    )
    world.say(
        f"At the same time, {hero.id} saw the {yoke.label} leaning crookedly, as if it had been bumped."
    )
    world.say(
        f"{sibling.label.capitalize()} whispered that it felt like a mystery, but a sad one, because nobody wanted the day to end with tears."
    )
    world.say(
        f"Near the dusty floor, {hero.id} spotted {clue.phrase}."
    )


def solve_mystery(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    sibling = world.facts["sibling"]
    award = world.facts["award"]
    yoke = world.facts["yoke"]
    clue = world.facts["clue"]
    notch = world.facts["notch"]

    if clue.points_to != award.id:
        raise StoryError("Bad mystery design: clue does not point to the award.")

    # The clue reveals the award was knocked behind the feed bin by the yoke.
    award.meters["hidden"] = 0.0
    award.meters["found"] = 1.0
    yoke.meters["damaged"] = 0.0
    yoke.meters["fixed"] = 1.0
    notch.meters["seen"] = 1.0

    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    hero.memes["pride"] = 1.0
    parent.memes["worry"] = 0.0
    parent.memes["comfort"] = 1.0
    sibling.memes["hope"] = 1.0

    world.para()
    world.say(
        f"{hero.id} followed the sawdust trail and found the {award.label} tucked behind the feed bin."
    )
    world.say(
        f"The little {notch.label} on the {yoke.label} matched the scratch on the bin, so the family knew the yoke had bumped the award by accident."
    )
    world.say(
        f"{parent.id} smiled, and {sibling.label} clapped because the mystery was solved before the evening bell."
    )
    world.say(
        f"Then {hero.id} wiped the dust from the {award.label}, and the {yoke.label} was fixed and set straight again."
    )


def ending(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    award = world.facts["award"]
    yoke = world.facts["yoke"]

    world.para()
    world.say(
        f"That night, the {award.label} hung where everyone could see it, and the {yoke.label} rested safely by the wall."
    )
    world.say(
        f"{hero.id} felt warm and proud, because the family had turned a bad-ending worry into a happy answer together."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    if world.facts["award"].meters["hidden"] < THRESHOLD:
        raise StoryError("Story setup failed: award should start hidden.")
    intro(world)
    build_conflict(world)
    solve_mystery(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming mystery story for a child about a missing {f['award'].label} and a {f['yoke'].label}.",
        f"Tell a short story where {f['hero'].id} solves a barnyard mystery by noticing a {f['notch'].label}.",
        f"Make a gentle story in which a lost {f['award'].label} is found and a broken-looking {f['yoke'].label} is explained.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    award = f["award"]
    yoke = f["yoke"]
    notch = f["notch"]

    return [
        QAItem(
            question=f"What mystery did {hero.id} notice at {world.place.label}?",
            answer=f"{hero.id} noticed that the {award.label} was missing and the {yoke.label} looked bumped and strange.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the problem?",
            answer=f"A little trail of sawdust and the {notch.label} on the {yoke.label} helped explain what happened.",
        ),
        QAItem(
            question=f"What was the cause of the mystery?",
            answer=f"The {yoke.label} had bumped the {award.label} behind the feed bin by accident.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The {award.label} was found, the {yoke.label} was fixed, and {hero.id} felt proud and relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yoke?",
            answer="A yoke is a bar or harness used to help carry, pull, or balance a load.",
        ),
        QAItem(
            question="What is an award?",
            answer="An award is something given to praise someone for doing a good job.",
        ),
        QAItem(
            question="What is a notch?",
            answer="A notch is a small cut, dent, or opening in something solid.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is active when the award is hidden and the yoke has a notch.
mystery_active :- hidden(award), notched(yoke).

% The clue works if it points to the award and the award was hidden.
clue_valid :- clue_points_to(clue1, award), hidden(award).

% The mystery is solved if the clue is valid and the yoke is fixed.
solved :- clue_valid, fixed(yoke).

% A bad ending is avoided when the mystery is solved.
happy_end :- solved.

#show mystery_active/0.
#show clue_valid/0.
#show solved/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hidden", "award"),
        asp.fact("notched", "yoke"),
        asp.fact("clue_points_to", "clue1", "award"),
        asp.fact("fixed", "yoke"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = {atom.name for atom in model}
    required = {"mystery_active", "clue_valid", "solved", "happy_end"}
    if required.issubset(shown):
        print("OK: ASP twin produces the expected solved happy ending.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected facts.")
    print("Shown:", sorted(shown))
    return 1


# ---------------------------------------------------------------------------
# Emit / trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={ {k: v for k, v in e.meters.items() if v} }")
        if e.memes:
            parts.append(f"memes={ {k: v for k, v in e.memes.items() if v} }")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.type} " + " ".join(parts))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming mystery storyworld with yoke, award, and notch.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--sibling", choices=["sister", "brother"])
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
    return make_story_params(rng, args)


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


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="barn", hero_name="Maya", hero_gender="girl", parent_type="mother", sibling_type="brother"),
        StoryParams(place="yard", hero_name="Theo", hero_gender="boy", parent_type="father", sibling_type="sister"),
        StoryParams(place="stable", hero_name="Nora", hero_gender="girl", parent_type="father", sibling_type="sister"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        print(asp_program())
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i - 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
