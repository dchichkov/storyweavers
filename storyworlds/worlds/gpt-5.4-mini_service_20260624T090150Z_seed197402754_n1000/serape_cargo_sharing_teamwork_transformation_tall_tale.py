#!/usr/bin/env python3
"""
Tall-tale storyworld: a serape, a cargo load, and a transformation brought by sharing and teamwork.

Seed inspiration:
- A wide serape and a heavy cargo load are in trouble.
- Several helpers learn to share the load.
- Their teamwork transforms what looked impossible into a cheerful, finished journey.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Character:
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ObjectThing:
    name: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: list[str] = field(default_factory=list)
    state: str = "plain"


@dataclass
class StoryParams:
    place: str
    cargo: str
    hero: str
    helper1: str
    helper2: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    hero: Character
    helper1: Character
    helper2: Character
    serape: ObjectThing
    cargo: ObjectThing
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for obj in [self.hero, self.helper1, self.helper2, self.serape, self.cargo]:
            meters = {k: v for k, v in obj.meters.items() if v}
            memes = {k: v for k, v in obj.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if getattr(obj, "carried_by", None):
                bits.append(f"carried_by={obj.carried_by}")
            if getattr(obj, "state", None):
                bits.append(f"state={obj.state}")
            lines.append(f"  {obj.name:10} ({obj.kind:9}) {' '.join(bits)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "mesa": "the windy mesa",
    "market": "the bright market square",
    "harbor": "the harbor road",
    "trail": "the long dusty trail",
}

CARGOES = {
    "melons": ("a wagon of melons", 3.0),
    "tiles": ("a stack of clay tiles", 4.0),
    "books": ("a crate of storybooks", 2.0),
    "lanterns": ("a bundle of lanterns", 2.5),
}

HEROES = ["Marta", "Javi", "Nina", "Tomas"]
HELPERS = ["Luz", "Paco", "Rita", "Benito"]

# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def build_world(params: StoryParams) -> World:
    hero = Character(name=params.hero, role="leader", meters={"strain": 0.0}, memes={"hope": 1.0})
    helper1 = Character(name=params.helper1, role="helper", meters={"strain": 0.0}, memes={"helping": 0.0})
    helper2 = Character(name=params.helper2, role="helper", meters={"strain": 0.0}, memes={"helping": 0.0})
    serape = ObjectThing(name="serape", owner=hero.name, meters={"weight": 0.0}, memes={"pride": 1.0}, state="wrapped")
    cargo_label, cargo_weight = CARGOES[params.cargo]
    cargo = ObjectThing(name=params.cargo, owner=hero.name, meters={"weight": cargo_weight}, memes={"value": 1.0}, state="stuck")
    w = World(place=PLACES[params.place], hero=hero, helper1=helper1, helper2=helper2, serape=serape, cargo=cargo)
    w.facts.update(params=params, cargo_label=cargo_label)
    return w


def narrate_setup(world: World) -> None:
    h = world.hero
    c = world.cargo
    world.say(
        f"On {world.place}, {h.name} wore a bright serape that fluttered like a flag in a storm."
    )
    world.say(
        f"Beside {h.name} sat {world.facts['cargo_label']}, so heavy it might have been carved out of thunder."
    )


def apply_burden(world: World) -> None:
    h = world.hero
    c = world.cargo
    h.meters["strain"] += c.meters["weight"] / 2.0
    h.memes["worry"] = h.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{h.name} tried to move {c.name}, but the load would not budge and only made {h.name} breathe hard."
    )


def offer_sharing(world: World) -> None:
    h, a, b = world.hero, world.helper1, world.helper2
    world.say(
        f"Then {a.name} and {b.name} came along, and they did not laugh; they smiled the kind smile of people ready to share a hard job."
    )
    world.say(
        f'“A load is lighter when hearts are willing,” said {a.name}. “And a serape can become a plan if three hands hold it true.”'
    )
    h.memes["hope"] += 1.0
    a.memes["helping"] += 1.0
    b.memes["helping"] += 1.0


def teamwork_transform(world: World) -> None:
    h, a, b = world.hero, world.helper1, world.helper2
    c = world.cargo
    s = world.serape

    # Sharing the serape as a sling and the cargo as a shared burden.
    s.state = "shared-sling"
    c.carried_by = [h.name, a.name, b.name]
    h.meters["strain"] = max(0.0, h.meters["strain"] - 0.8)
    a.meters["strain"] += 0.4
    b.meters["strain"] += 0.4
    c.state = "moving"

    world.say(
        f"So they spread the serape wide, tucked the cargo safe in the middle, and turned cloth into a cradle."
    )
    world.say(
        f"With one step from each of them, the impossible load started rolling as if it had grown friendly feet."
    )

    # Transformation: what seemed like a burden becomes a gift.
    c.memes["value"] += 1.0
    s.memes["pride"] += 1.0
    c.state = "delivered"
    s.state = "banner"
    world.say(
        f"By the end, the cargo was delivered, the serape flew like a banner, and the whole road seemed taller for having seen such teamwork."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    world.para()
    apply_burden(world)
    offer_sharing(world)
    world.para()
    teamwork_transform(world)
    world.facts.update(
        shared=True,
        transformed=True,
        burden=max(world.hero.meters.get("strain", 0.0), 0.0),
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a tall-tale story about {p.hero}, a serape, and {world.facts['cargo_label']} on {world.place} that celebrates sharing and teamwork.",
        f"Tell a child-friendly story in which {p.hero} cannot move a heavy cargo alone, but friends turn the serape into a clever helper.",
        "Write a short tall tale where a cloth and a heavy load are transformed by kindness and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    cargo_label = world.facts["cargo_label"]
    return [
        QAItem(
            question=f"What was {p.hero} trying to move at the beginning of the story?",
            answer=f"{p.hero} was trying to move {cargo_label}, but it was far too heavy to handle alone.",
        ),
        QAItem(
            question="How did the friends use the serape?",
            answer="They spread the serape wide and used it like a shared sling to carry the cargo together.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The cargo was delivered, the serape became a proud banner, and the hard job turned into a successful team effort.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use, hold, or enjoy something together instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and each one helps with the job.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state into another, like turning a plain cloth into a useful banner or sling.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin and validation
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_place/1.
#show valid_story/3.

valid_place(mesa).
valid_place(market).
valid_place(harbor).
valid_place(trail).

cargo(melons).
cargo(tiles).
cargo(books).
cargo(lanterns).

valid_story(P, C, F) :- valid_place(P), cargo(C), feature(F).
feature(sharing).
feature(teamwork).
feature(transformation).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for p in PLACES:
        lines.append(asp.fact("valid_place", p))
    for c in CARGOES:
        lines.append(asp.fact("cargo", c))
    for f in ["sharing", "teamwork", "transformation"]:
        lines.append(asp.fact("feature", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c, f) for p in PLACES for c in CARGOES for f in ["sharing", "teamwork", "transformation"]}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP parity matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params, generation, emit
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: serape, cargo, sharing, teamwork, transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper1", choices=HELPERS)
    ap.add_argument("--helper2", choices=HELPERS)
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
    cargo = args.cargo or rng.choice(list(CARGOES))
    hero = args.hero or rng.choice(HEROES)
    helpers = [h for h in HELPERS if h != hero]
    helper1 = args.helper1 or rng.choice(helpers)
    helpers2 = [h for h in helpers if h != helper1]
    helper2 = args.helper2 or rng.choice(helpers2)
    if len({hero, helper1, helper2}) < 3:
        raise StoryError("The hero and both helpers must be different characters.")
    return StoryParams(place=place, cargo=cargo, hero=hero, helper1=helper1, helper2=helper2)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="mesa", cargo="melons", hero="Marta", helper1="Luz", helper2="Paco"),
    StoryParams(place="market", cargo="books", hero="Javi", helper1="Rita", helper2="Benito"),
    StoryParams(place="harbor", cargo="lanterns", hero="Nina", helper1="Paco", helper2="Luz"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, cargo, feature) triples:\n")
        for place, cargo, feat in stories:
            print(f"  {place:8} {cargo:10} {feat}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
