#!/usr/bin/env python3
"""
storyworlds/worlds/teeter_sharing_tall_tale.py
==============================================

A tall-tale story world about sharing a teeter-totter.

Premise:
- A child wants to teeter on a giant seesaw with a prized treat.
- The tale turns when the load is lopsided or the treat is hard to share.
- The resolution comes from a sharing act that makes the teetering fair.

The world keeps track of:
- physical meters: balance, snack, reach, lift, wobble
- emotional memes: joy, greed, patience, fairness, pride, gratitude

The prose is authored from the simulated state rather than from a fixed template.
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")


@dataclass
class Place:
    name: str
    height: str
    crowd: str
    afford_teeter: bool = True


@dataclass
class Shareable:
    id: str
    label: str
    phrase: str
    split_into: str
    fragility: str
    flavor: str
    weight: float = 1.0


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    gift: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        out: list[str] = []
        para: list[str] = []
        for line in self.lines:
            if line == "":
                if para:
                    out.append(" ".join(para))
                    para = []
            else:
                para.append(line)
        if para:
            out.append(" ".join(para))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "county_fair": Place(name="the county fair", height="sky-high", crowd="cheering"),
    "orchard_hill": Place(name="Orchard Hill", height="hill-high", crowd="windy"),
    "riverbank": Place(name="the riverbank", height="bridge-high", crowd="chatty"),
}

ENTITIES = {
    "giant_pie": Shareable(
        id="giant_pie",
        label="giant pie",
        phrase="a giant cherry pie",
        split_into="slice the pie into sharing slices",
        fragility="squishy",
        flavor="cherry",
        weight=3.0,
    ),
    "honey_cake": Shareable(
        id="honey_cake",
        label="honey cake",
        phrase="a golden honey cake",
        split_into="cut the cake into fair wedges",
        fragility="crumbly",
        flavor="honey",
        weight=2.0,
    ),
    "apple_bushel": Shareable(
        id="apple_bushel",
        label="bushel of apples",
        phrase="a bushel of shiny apples",
        split_into="divide the apples into neat piles",
        fragility="bouncy",
        flavor="apple",
        weight=1.5,
    ),
    "blueberry_tin": Shareable(
        id="blueberry_tin",
        label="blueberry tin",
        phrase="a tin full of blueberries",
        split_into="share the blueberries by the handful",
        fragility="spilly",
        flavor="blueberry",
        weight=1.2,
    ),
}

HEROES = [
    ("Nell", "girl"),
    ("Benny", "boy"),
    ("Mara", "girl"),
    ("Otis", "boy"),
    ("Pippa", "girl"),
]
SIDEKICKS = [
    ("Wren", "girl"),
    ("Jojo", "boy"),
    ("Midge", "girl"),
    ("Toby", "boy"),
    ("Lulu", "girl"),
]
TRAITS = ["bold", "bright-eyed", "spry", "curious", "plucky"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, gift: str) -> bool:
    return place in PLACES and gift in ENTITIES and PLACES[place].afford_teeter


def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p in PLACES for g in ENTITIES if valid_combo(p, g)]


def reason_invalid(place: str, gift: str) -> str:
    return f"(No story: the board at {place} cannot safely host {gift}.)"


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def _seed_phrase(seed: int) -> str:
    if seed % 3 == 0:
        return "as if the wind itself had learned to grin"
    if seed % 3 == 1:
        return "with a bounce big enough to wake the crows"
    return "like a drumbeat under a fairground moon"


def describe_place(place: Place) -> str:
    return f"{place.name.capitalize()} was {place.height}, and the air was {place.crowd}."


def start_story(hero: Entity, sidekick: Entity, gift: Shareable, place: Place, trait: str, seed: int) -> list[str]:
    return [
        f"Little {trait} {hero.id} loved to teeter on the old seesaw at {place.name}.",
        f"{hero.pronoun('possessive').capitalize()} friend {sidekick.id} loved to watch the board rise and fall, {_seed_phrase(seed)}.",
        f"One day they came with {gift.phrase}, because they both thought a big day ought to begin with a big treat.",
    ]


def want_share(hero: Entity, gift: Shareable) -> str:
    hero.memes["greed"] = hero.memes.get("greed", 0) + 1
    return f"{hero.id} wanted to keep the {gift.label} close while {hero.pronoun()} teetered."


def notice_problem(world: World, hero: Entity, sidekick: Entity, gift: Shareable) -> str:
    board = world.facts["balance"]
    if board < 0.5:
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1
        return (
            f"But the board dipped too far on {hero.id}'s side, and the whole contraption "
            f"wobbled like a kite in a thunderstorm."
        )
    return (
        f"But the treat was too fine to enjoy alone, and {sidekick.id} looked at it with "
        f"a hopeful face."
    )


def share_turn(world: World, hero: Entity, sidekick: Entity, gift: Shareable) -> str:
    hero.memes["patience"] = hero.memes.get("patience", 0) + 1
    sidekick.memes["gratitude"] = sidekick.memes.get("gratitude", 0) + 1
    world.facts["shared"] = True
    world.facts["balance"] = 1.0
    world.facts["treat_state"] = "shared"
    return (
        f"{hero.id} laughed, broke the {gift.label} into fair pieces, and handed one to {sidekick.id}. "
        f"That was enough to make the seesaw settle true."
    )


def ending(world: World, hero: Entity, sidekick: Entity, gift: Shareable) -> str:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0) + 1
    return (
        f"Soon {hero.id} and {sidekick.id} were teetering together, one piece of {gift.label} in each hand, "
        f"and the tall board sang up and down as neatly as a swing in the sky."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    gift = ENTITIES[params.gift]
    hero_name = params.hero
    sidekick_name = params.sidekick
    hero_type = "girl" if hero_name in {"Nell", "Mara", "Pippa"} else "boy"
    sidekick_type = "girl" if sidekick_name in {"Wren", "Midge", "Lulu"} else "boy"

    world = World(place=place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type, meters={}, memes={}))

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        gift=gift,
        place=place,
        balance=0.25 if gift.weight >= 2.5 else 0.75,
        shared=False,
        treat_state="whole",
        trait=params.seed if params.seed is not None else 0,
    )

    world.say(describe_place(place))
    for s in start_story(hero, sidekick, gift, place, TRAITS[abs(hash(hero_name)) % len(TRAITS)], params.seed or 0):
        world.say(s)

    world.say(want_share(hero, gift))
    world.say(notice_problem(world, hero, sidekick, gift))
    world.say(share_turn(world, hero, sidekick, gift))
    world.say(ending(world, hero, sidekick, gift))
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A gift is reasonable to teeter with when the place can host a seesaw.
valid(Place, Gift) :- place(Place), gift(Gift), affords_teeter(Place).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].afford_teeter:
            lines.append(asp.fact("affords_teeter", p))
    for g in ENTITIES:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    gift = f["gift"]
    place = f["place"]
    return [
        f'Write a short tall tale about a child named {hero.id} who wants to teeter at {place.name}.',
        f"Tell a sharing story where {hero.id} and {sidekick.id} learn to share {gift.phrase} on a seesaw.",
        f"Write a child-friendly story that includes teetering, a giant treat, and a fair way to share.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    gift = f["gift"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {sidekick.id} go to teeter?",
            answer=f"They went to {place.name}, where the seesaw could rise and dip like a barn door in a storm wind.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {gift.label} at first?",
            answer=f"{hero.id} wanted to keep the {gift.label} close while teetering, which made the board lean too hard.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {sidekick.id}?",
            answer=f"They shared the {gift.label}, and then they teetered together with the board balanced again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else have part of something instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is a teeter-totter?",
            answer="A teeter-totter is a long board that goes up and down when two riders sit on opposite ends.",
        ),
        QAItem(
            question="Why does sharing help on a teeter-totter?",
            answer="Sharing can make the weight more even, which helps the board balance and makes play kinder for everyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale sharing storyworld with teetering.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--gift", choices=sorted(ENTITIES))
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    combos = valid_combos()
    if args.place and args.gift and not valid_combo(args.place, args.gift):
        raise StoryError(reason_invalid(args.place, args.gift))
    filtered = [
        (p, g) for p, g in combos
        if (args.place is None or p == args.place)
        and (args.gift is None or g == args.gift)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, gift = rng.choice(filtered)
    hero = args.hero or rng.choice(HEROES)[0]
    sidekick = args.sidekick or rng.choice([x for x in SIDEKICKS if x[0] != hero])[0]
    return StoryParams(place=place, hero=hero, sidekick=sidekick, gift=gift)


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


CURATED = [
    StoryParams(place="county_fair", hero="Nell", sidekick="Jojo", gift="giant_pie"),
    StoryParams(place="orchard_hill", hero="Mara", sidekick="Lulu", gift="apple_bushel"),
    StoryParams(place="riverbank", hero="Otis", sidekick="Wren", gift="blueberry_tin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid teeter/sharing combos:")
        for p, g in combos:
            print(f"  {p:14} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
