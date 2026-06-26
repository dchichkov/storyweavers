#!/usr/bin/env python3
"""
Storyworld: Pirate Tale with a bandage, quick action, foreshadowing, a
misunderstanding, and a happy ending.

A small, constraint-checked domain:
- One pirate crew on a little ship near a quiet cove.
- A foreshadowed danger (a loose spar and a splinter).
- A misunderstanding about who broke the chart.
- A quick fix with a bandage and a truthful reveal.
- A happy ending with repaired trust and a safe sail.

The simulated world uses physical meters and emotional memes, and the prose is
driven by those state changes.
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
# Core world model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    mate_name: str
    mate_type: str
    seed: Optional[int] = None


PLACES = {
    "cove": "a quiet cove",
    "harbor": "the harbor",
    "ship": "a small ship",
}

HERO_TYPES = ["boy", "girl"]
MATE_TYPES = ["boy", "girl"]

NAMES = {
    "boy": ["Finn", "Jack", "Milo", "Nate", "Theo"],
    "girl": ["Mara", "Ruby", "Pia", "Lina", "Nell"],
}


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str


ITEMS = {
    "chart": Item(id="chart", label="chart", phrase="a folded sea chart", region="hands"),
    "bandage": Item(id="bandage", label="bandage", phrase="a clean bandage", region="hands"),
    "hat": Item(id="hat", label="hat", phrase="a striped pirate hat", region="head"),
}


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def _speech(name: str, line: str) -> str:
    return f'"{line}" {name} said.'


def tell(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "hurt": 0.0, "trust": 0.0},
    ))
    mate = world.add(Entity(
        id=params.mate_name,
        kind="character",
        type=params.mate_type,
        meters={},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "hurt": 0.0, "trust": 0.0},
    ))
    chart = world.add(Entity(
        id="chart",
        type="chart",
        label="chart",
        phrase="a folded sea chart",
        owner=hero.id,
        caretaker=hero.id,
        worn_by=hero.id,
    ))
    bandage = world.add(Entity(
        id="bandage",
        type="bandage",
        label="bandage",
        phrase="a clean bandage",
        owner=mate.id,
        caretaker=mate.id,
    ))
    hat = world.add(Entity(
        id="hat",
        type="hat",
        label="hat",
        phrase="a striped pirate hat",
        owner=hero.id,
        caretaker=hero.id,
        worn_by=hero.id,
    ))

    # Foreshadowing.
    world.say(
        f"On a little ship near {world.place}, {hero.id} and {mate.id} were ready for a pirate day."
    )
    world.say(
        f"The mast gave a small creak in the wind, and a sharp little splinter peeked from the rope."
    )
    world.say(
        f"{hero.id} saw it first, but only tucked the worry away for later."
    )

    world.para()

    # Misunderstanding.
    hero.memes["curiosity"] += 1.0
    mate.memes["worry"] += 1.0
    chart.meters["torn"] = 1.0  # a wind-flip causes trouble
    world.say(
        f"Then the wind whooshed hard, and the chart fluttered off the table."
    )
    world.say(
        f"When it landed, a corner tore."
    )
    world.say(
        f"{mate.id} looked at the torn chart and thought {hero.id} had been too rough with it."
    )
    hero.memes["hurt"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"{hero.id} frowned, because {hero.pronoun('subject')} had not done it at all."
    )

    world.para()

    # Quick action and bandage.
    hero.meters["splinter"] = 1.0
    hero.meters["pain"] = 1.0
    hero.memes["hurt"] += 1.0
    world.say(
        f"While they argued, the tiny splinter snapped into {hero.pronoun('possessive')} palm."
    )
    world.say(
        f"{mate.id} gasped, then moved quick as a gull."
    )
    bandage.worn_by = hero.id
    hero.meters["bandaged"] = 1.0
    hero.meters["pain"] = 0.0
    hero.memes["joy"] += 1.0
    mate.memes["trust"] += 1.0
    world.say(
        f"{mate.id} wrapped the clean bandage around {hero.pronoun('possessive')} hand."
    )
    world.say(
        f"The hurt eased right away, and the ship felt kinder."
    )

    # Truth and happy ending.
    hero.memes["trust"] += 1.0
    mate.memes["trust"] += 1.0
    world.para()
    world.say(
        f"{hero.id} pointed to the loose spar and explained the wind had torn the chart, not {hero.id}."
    )
    world.say(
        f"{mate.id} listened, blinked, and looked ashamed for the mistake."
    )
    world.say(
        f"Then {mate.id} smiled and said { _speech(mate.id, 'I was quick to blame you. I am sorry') }"
    )
    world.say(
        f"{hero.id} nodded, forgave the mix-up, and tied the chart flat again."
    )
    world.say(
        f"By sunset, the two pirates were laughing, the bandage was neat and white, and their little ship sailed on in peace."
    )

    world.facts = {
        "hero": hero,
        "mate": mate,
        "chart": chart,
        "bandage": bandage,
        "hat": hat,
        "place": params.place,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    return [
        "Write a short pirate tale with a foreshadowed danger, a misunderstanding, a bandage, and a happy ending.",
        f"Tell a child-friendly story where {hero.id} and {mate.id} sail near a cove, get mixed up about a torn chart, and then make things right quickly.",
        "Write a small pirate story that includes a clean bandage and ends with friends sailing away smiling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    chart = f["chart"]
    bandage = f["bandage"]
    return [
        QAItem(
            question=f"What was foreshadowed at the start of the pirate tale?",
            answer="A loose mast splinter and a windy day hinted that something tricky might happen later.",
        ),
        QAItem(
            question=f"Why did {mate.id} think {hero.id} had caused the trouble with the chart?",
            answer=f"{mate.id} saw the torn chart after the wind blew and made a quick mistake, so {mate.id} blamed {hero.id} too soon.",
        ),
        QAItem(
            question=f"What did {mate.id} use to help {hero.id}'s hand?",
            answer=f"{mate.id} used a clean bandage to wrap {hero.id}'s hurt hand and make it feel better quickly.",
        ),
        QAItem(
            question=f"How did the story end for the two pirates?",
            answer=f"They told the truth, forgave the misunderstanding, and sailed away happy together on their little ship.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bandage for?",
            answer="A bandage is a soft strip used to cover a small hurt and help it heal.",
        ),
        QAItem(
            question="Why is being quick helpful in an emergency?",
            answer="Being quick helps someone give care sooner, which can stop a small problem from becoming a bigger one.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing because they do not have all the facts yet.",
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
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when it has a foreshadowed hazard, a misunderstanding,
% a bandage moment, and a happy ending.
valid_story(P) :- place(P), foreshadow(P), misunderstanding(P), bandage_help(P), happy_ending(P).

% The bandage helps only if a hand is hurt and the bandage is available.
bandage_help(P) :- hurt_hand(P), has_bandage(P).

% A misunderstanding is reasonable when a torn chart is blamed on the wrong pirate.
misunderstanding(P) :- torn_chart(P), false_blame(P).

% Foreshadowing requires an early hazard.
foreshadow(P) :- loose_splinter(P).

% Happy ending means the blame is corrected and trust rises.
happy_ending(P) :- corrected_blame(P), trust_restored(P).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("loose_splinter", "cove"))
    lines.append(asp.fact("torn_chart", "cove"))
    lines.append(asp.fact("false_blame", "cove"))
    lines.append(asp.fact("hurt_hand", "cove"))
    lines.append(asp.fact("has_bandage", "cove"))
    lines.append(asp.fact("corrected_blame", "cove"))
    lines.append(asp.fact("trust_restored", "cove"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {"cove"}
    asp_set = {p[0] for p in asp_valid_places()}
    if py == asp_set:
        print("OK: ASP and Python agree on valid story places.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", sorted(py))
    print("asp:", sorted(asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story sampling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with bandage, quick action, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--mate-name")
    ap.add_argument("--mate-type", choices=MATE_TYPES)
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
    place = args.place or rng.choice(list(PLACES))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    mate_type = args.mate_type or rng.choice(MATE_TYPES)
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    mate_name = args.mate_name or rng.choice([n for n in NAMES[mate_type] if n != hero_name] or NAMES[mate_type])
    if hero_name == mate_name:
        raise StoryError("The hero and mate must have different names.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        mate_name=mate_name,
        mate_type=mate_type,
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {', '.join(bits)}")
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
    StoryParams(place="cove", hero_name="Finn", hero_type="boy", mate_name="Mara", mate_type="girl"),
    StoryParams(place="harbor", hero_name="Ruby", hero_type="girl", mate_name="Jack", mate_type="boy"),
    StoryParams(place="ship", hero_name="Nate", hero_type="boy", mate_name="Lina", mate_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.mate_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
