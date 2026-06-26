#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hinder_fee_predicament_conflict_inner_monologue_mystery.py
===============================================================================================================================

A small mystery storyworld with a child-facing, state-driven conflict:
a fee goes missing, a clue hunt is hindered, and an inner monologue helps
the protagonist think through a predicament and solve it.

The story logic models:
- physical meters: distance, blocked_access, hiddenness, tidiness, possession
- emotional memes: worry, confidence, conflict, curiosity, relief
- a mystery premise with a failed path, an inner thought turn, and a resolution
  that reveals what was really causing the problem.

This file is standalone and uses only the stdlib plus the shared result
containers, with lazy ASP import for verification mode.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    clues: set[str] = field(default_factory=set)
    hiding_spots: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry data
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    protagonist: str
    role: str
    culprit: str
    fee_item: str
    clue_item: str
    seed: Optional[int] = None


SETTINGS = {
    "lobby": Place(
        name="the school lobby",
        indoors=True,
        clues={"notice board", "front desk", "shoe rack"},
        hiding_spots={"notice board", "bench", "plant"},
    ),
    "library": Place(
        name="the quiet library",
        indoors=True,
        clues={"return cart", "dusty shelf", "reading nook"},
        hiding_spots={"return cart", "riddle book", "chair"},
    ),
    "museum": Place(
        name="the small museum",
        indoors=True,
        clues={"ticket booth", "glass case", "map stand"},
        hiding_spots={"ticket booth", "poster", "guide desk"},
    ),
}

CHARACTER_TYPES = {
    "girl": ["Mina", "Nina", "Tara", "Lia", "Ruby"],
    "boy": ["Owen", "Eli", "Noah", "Jasper", "Theo"],
}

ROLES = ["young detective", "curious helper", "little sleuth", "patient finder"]

CULPRITS = {
    "cat": "a striped cat",
    "wind": "a sneaky wind puff",
    "brother": "the older brother",
    "teacher": "the teacher",
}

FEE_ITEMS = {
    "entry_fee": ("entry fee", "the small entry fee"),
    "library_fee": ("library fee", "the library fee"),
    "ticket_fee": ("ticket fee", "the ticket fee"),
}

CLUE_ITEMS = {
    "receipt": ("receipt", "the crumpled receipt"),
    "token": ("token", "the little metal token"),
    "note": ("note", "the folded note"),
}


# ---------------------------------------------------------------------------
# Story state helpers
# ---------------------------------------------------------------------------
def pronounce_name(name: str, role: str) -> str:
    return f"{name}, the {role}"


def inner_monologue(world: World, hero: Entity, fee: Entity, clue: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} looked at the missing {fee.label} and thought, "
        f'"If I was the clue, where would I hide?"'
    )
    world.say(
        f'In {hero.pronoun("possessive")} head, another thought answered, '
        f'"Not far. The answer is probably close to the place that matters most."'
    )
    clue.hidden = False
    clue.meters["hiddenness"] = 0.0


def search(world: World, hero: Entity, place: Place, culprit: Entity, clue: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} searched around {place.name}, checking each likely hiding spot."
    )
    for spot in sorted(place.hiding_spots):
        if ("search", spot) in world.fired:
            continue
        world.fired.add(("search", spot))
        world.say(f"{hero.pronoun().capitalize()} looked behind the {spot}.")
        if spot == clue.phrase:
            world.say(f"There, {hero.id} found the {clue.label} tucked away near the {spot}.")
            break
    if culprit.id == "wind":
        culprit.memes["suspicion"] += 1


def reveal(world: World, hero: Entity, fee: Entity, culprit: Entity, clue: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["conflict"] = 0.0
    fee.hidden = False
    fee.carried_by = hero.id
    world.say(
        f"Then the mystery clicked into place: the {fee.label} had not been stolen at all."
    )
    world.say(
        f"It had slipped near the {clue.phrase}, and the little clue had hidden the problem in plain sight."
    )
    world.say(
        f"{hero.id} smiled, paid the {fee.label}, and felt the whole predicament melt away."
    )


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    place = SETTINGS[params.setting]
    world = World(place)

    hero = world.add(Entity(
        id=params.protagonist,
        kind="character",
        type="girl" if params.role in {"young detective", "little sleuth"} else "boy",
        label=params.protagonist,
        meters={"distance": 0.0},
        memes={"worry": 0.0, "curiosity": 1.0, "conflict": 0.0, "relief": 0.0},
    ))
    culprit = world.add(Entity(
        id=params.culprit,
        kind="character" if params.culprit in {"brother", "teacher"} else "thing",
        type="boy" if params.culprit == "brother" else "cat" if params.culprit == "cat" else "thing",
        label=CULPRITS[params.culprit],
        memes={"suspicion": 0.0},
    ))
    fee_label, fee_phrase = FEE_ITEMS[params.fee_item]
    clue_label, clue_phrase = CLUE_ITEMS[params.clue_item]

    fee = world.add(Entity(
        id="fee",
        type="money",
        label=fee_label,
        phrase=fee_phrase,
        owner=hero.id,
        hidden=True,
        meters={"hiddenness": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="paper",
        label=clue_label,
        phrase=clue_phrase,
        owner=hero.id,
        hidden=True,
        meters={"hiddenness": 1.0},
    ))

    # Setup
    world.say(
        f"{hero.id} was a {params.role} at {place.name}, and {hero.pronoun()} loved solving small mysteries."
    )
    world.say(
        f"That day, {hero.pronoun('possessive')} biggest problem was a missing {fee.label}."
    )
    world.para()

    # Conflict
    world.say(
        f"{hero.id} checked the front of the room, but something kept hindering the search."
    )
    hero.memes["conflict"] += 1
    world.say(
        f"A muddled feeling grew in {hero.pronoun('possessive')} chest: {hero.pronoun()} could not tell whether the {fee.label} was lost, moved, or hidden."
    )
    world.say(
        f"{hero.id} noticed a {clue.label} nearby, but it was tucked where it was easy to miss."
    )
    world.para()

    # Turn via inner monologue
    inner_monologue(world, hero, fee, clue)
    search(world, hero, place, culprit, clue)
    world.para()

    # Resolution
    reveal(world, hero, fee, culprit, clue)
    world.say(
        f"In the end, the mystery was small, but {hero.pronoun('possessive')} careful thinking made it feel big and brave."
    )

    world.facts.update(
        hero=hero,
        culprit=culprit,
        fee=fee,
        clue=clue,
        place=place,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# Quality / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story about "{f["hero"].id}" where a missing {f["fee"].label} causes trouble and an inner monologue helps solve it.',
        f'Write a short story set in {f["place"].name} with a hidden clue, a hindered search, and a calm ending.',
        f'Tell a gentle detective story that uses the words "hinder", "fee", and "predicament" naturally.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    fee: Entity = f["fee"]
    clue: Entity = f["clue"]
    place: Place = f["place"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What was {hero.id}'s predicament in {place.name}?",
            answer=f"{hero.id} was trying to solve the mystery of a missing {fee.label}, which was causing a tricky predicament at {place.name}.",
        ),
        QAItem(
            question=f"How did {hero.id} think through the problem when the search was hindered?",
            answer=f"{hero.id} used an inner monologue and asked where the clue might hide, then looked in the most likely spots near {clue.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} discover about the missing {fee.label}?",
            answer=f"{hero.id} discovered that the {fee.label} was not stolen; it had simply slipped near the clue and was hidden close by.",
        ),
        QAItem(
            question=f"Why did the mystery matter to {hero.id}?",
            answer=f"{hero.id} needed the {fee.label} to be found so the day could continue, and the missing payment made the whole scene feel serious to a {params.role}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem with something hidden or unknown, and people try to find clues to understand it.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in a character's head, where the character thinks through a problem quietly.",
        ),
        QAItem(
            question="What does it mean to hinder something?",
            answer="To hinder something means to make it harder or slower, like when a blocked path makes a search take longer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.hidden:
            bits.append("hidden=True")
        parts.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

place(P) :- setting(P).
valid_story(P, Hero, Fee, Culprit) :- setting(P), protagonist(Hero), fee_item(Fee), culprit(Culprit).

% The declarative twin simply confirms there is at least one valid story
% for each registered combination.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, place in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if place.indoors:
            lines.append(asp.fact("indoors", sid))
        for clue in sorted(place.clues):
            lines.append(asp.fact("clue_spot", sid, clue))
        for spot in sorted(place.hiding_spots):
            lines.append(asp.fact("hiding_spot", sid, spot))
    for role in ROLES:
        lines.append(asp.fact("role", role))
    for g, names in CHARACTER_TYPES.items():
        lines.append(asp.fact("gender", g))
        for name in names:
            lines.append(asp.fact("name", name))
    for k in FEE_ITEMS:
        lines.append(asp.fact("fee_item", k))
    for k in CLUE_ITEMS:
        lines.append(asp.fact("clue_item", k))
    for k in CULPRITS:
        lines.append(asp.fact("culprit", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_count = len(valid_combos())
    asp_count = len(asp_valid_stories())
    if python_count == asp_count:
        print(f"OK: ASP and Python agree on {python_count} valid story families.")
        return 0
    print(f"MISMATCH: Python={python_count}, ASP={asp_count}")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for protagonist_gender in CHARACTER_TYPES:
            for role in ROLES:
                for culprit in CULPRITS:
                    combos.append((setting, protagonist_gender, role, culprit))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested options do not form a reasonable mystery.)"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with conflict and inner monologue."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--gender", choices=sorted(CHARACTER_TYPES))
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--fee-item", dest="fee_item", choices=sorted(FEE_ITEMS))
    ap.add_argument("--clue-item", dest="clue_item", choices=sorted(CLUE_ITEMS))
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(list(CHARACTER_TYPES))
    role = args.role or rng.choice(ROLES)
    culprit = args.culprit or rng.choice(list(CULPRITS))
    fee_item = args.fee_item or rng.choice(list(FEE_ITEMS))
    clue_item = args.clue_item or rng.choice(list(CLUE_ITEMS))
    name = args.name or rng.choice(CHARACTER_TYPES[gender])
    return StoryParams(
        setting=setting,
        protagonist=name,
        role=role,
        culprit=culprit,
        fee_item=fee_item,
        clue_item=clue_item,
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
    StoryParams(setting="lobby", protagonist="Mina", role="young detective", culprit="cat", fee_item="entry_fee", clue_item="receipt"),
    StoryParams(setting="library", protagonist="Owen", role="little sleuth", culprit="wind", fee_item="library_fee", clue_item="note"),
    StoryParams(setting="museum", protagonist="Tara", role="curious helper", culprit="brother", fee_item="ticket_fee", clue_item="token"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} valid story family entries.")
        for item in models:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
