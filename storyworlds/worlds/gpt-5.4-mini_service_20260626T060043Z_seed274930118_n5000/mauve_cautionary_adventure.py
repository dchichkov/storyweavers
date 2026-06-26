#!/usr/bin/env python3
"""
mauve_cautionary_adventure.py
=============================

A small Storyweavers world about a cautious adventure with a mauve object,
where curiosity can lead somewhere surprising, but warnings and preparation
turn it into a safe, satisfying outing.

Premise:
- A child longs for a mauve treasure and wants to take it on an adventure.
- The treasure is fragile, tempting, or easy to lose in a risky place.
- A careful helper warns about the danger and offers a safer plan.
- The story resolves when the child follows the caution and still gets the
  feeling of adventure.

This world is designed to feel like a tiny adventure tale with a cautionary
turn: excitement, warning, a change of plan, and a proof-of-safety ending.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    brittle: bool = False
    loss_risk: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    risky: bool = False
    details: str = ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    fragile: bool
    risky_place: str
    safe_place: str
    issue: str
    fix: str


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "wharf": Place(
        id="wharf",
        label="the wharf",
        risky=True,
        details="The boards by the water creaked, and the tide pulled at little gaps.",
    ),
    "cave": Place(
        id="cave",
        label="the cave trail",
        risky=True,
        details="The trail twisted under dark rock, with loose stones underfoot.",
    ),
    "forest": Place(
        id="forest",
        label="the forest path",
        risky=True,
        details="The path was narrow, and brambles tugged at anything carried too low.",
    ),
    "hill": Place(
        id="hill",
        label="the windy hill",
        risky=True,
        details="The hill was open to gusts that loved to snatch light things away.",
    ),
    "garden": Place(
        id="garden",
        label="the garden gate",
        risky=False,
        details="The garden was calm, with a low wall and a smooth little path.",
    ),
}

ITEMS = {
    "mauve_map": Item(
        id="mauve_map",
        label="mauve map",
        phrase="a folded mauve map with a silver line on it",
        fragile=True,
        risky_place="cave",
        safe_place="garden",
        issue="could tear or smudge",
        fix="put it in a stiff pouch and take the safe path",
    ),
    "mauve_kite": Item(
        id="mauve_kite",
        label="mauve kite",
        phrase="a bright mauve kite with a long ribbon tail",
        fragile=False,
        risky_place="hill",
        safe_place="garden",
        issue="could blow away",
        fix="wait for a calm day and hold the spool tightly",
    ),
    "mauve_lantern": Item(
        id="mauve_lantern",
        label="mauve lantern",
        phrase="a small mauve lantern with a glass belly",
        fragile=True,
        risky_place="wharf",
        safe_place="garden",
        issue="could crack on the boards",
        fix="carry it in both hands and keep it away from the edge",
    ),
    "mauve_shell": Item(
        id="mauve_shell",
        label="mauve shell",
        phrase="a little mauve shell that shimmered like a pearl",
        fragile=True,
        risky_place="forest",
        safe_place="garden",
        issue="could get lost in the leaves",
        fix="keep it in a box and visit the path first",
    ),
}

NAMES = {
    "girl": ["Mia", "Ava", "Zoe", "Lina", "Nora", "Ivy"],
    "boy": ["Leo", "Ben", "Theo", "Finn", "Owen", "Max"],
}
HELPERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["curious", "brave", "eager", "lively", "thoughtful", "restless"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_is_reasonable(place: Place, item: Item) -> bool:
    return place.risky or place.id == item.safe_place or place.id == item.risky_place


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            if story_is_reasonable(place, item):
                out.append((pid, iid))
    return out


def explain_rejection(place: Place, item: Item) -> str:
    return (
        f"(No story: {item.label} does not create a cautionary adventure at {place.label}. "
        f"Try a risky place like {item.risky_place.replace('_', ' ')} or choose a different item.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), 'curious')} {hero.type} "
        f"who loved {item.label} more than anything else."
    )
    world.say(
        f"{helper.label.capitalize()} had given {hero.pronoun('object')} {item.phrase}, and {hero.id} carried it everywhere."
    )


def adventure_pull(world: World, hero: Entity, place: Place, item: Entity) -> None:
    world.para()
    world.say(
        f"One day, {hero.id} wanted an adventure at {place.label}."
    )
    world.say(place.details)
    world.say(
        f"{hero.id} wanted to take the {item.label} along, because {item.pronoun('possessive')} mauve shine made the day feel exciting."
    )


def warn(world: World, helper: Entity, hero: Entity, item: Entity, place: Place) -> None:
    risk = item.issue
    world.say(
        f'"Careful," {helper.pronoun("subject")} said. "At {place.label}, your {item.label} might {risk}."'
    )
    world.facts["risk"] = risk
    world.facts["place_name"] = place.label


def choose_safer_plan(world: World, helper: Entity, hero: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} looked at the mauve treasure, then at {helper.label}, and nodded."
    )
    world.say(
        f'"Then let’s {item.fix}," {hero.pronoun("subject")} said, "so we can still have an adventure."'
    )


def ending(world: World, hero: Entity, helper: Entity, item: Entity, place: Place) -> None:
    world.para()
    safe = item.safe_place
    world.say(
        f"Together they chose the safe way: they kept the {item.label} steady and stayed away from trouble."
    )
    if place.id == safe:
        world.say(
            f"At {place.label}, {hero.id} found a tiny adventure in every step, and the {item.label} stayed safe and bright."
        )
    else:
        world.say(
            f"Later, the {item.label} rested safely at the {safe.replace('_', ' ')} while {hero.id} smiled, ready for a wiser adventure next time."
        )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    item_cfg = ITEMS[params.item]
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
    ))
    item = world.add(Entity(
        id=item_cfg.id,
        type="treasure",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        brittle=item_cfg.fragile,
        loss_risk=True,
        owner=hero.id,
        caretaker=helper.id,
    ))

    intro(world, hero, helper, item)
    adventure_pull(world, hero, place, item)
    warn(world, helper, hero, item, place)
    choose_safer_plan(world, helper, hero, item)
    ending(world, hero, helper, item, place)

    world.facts.update(hero=hero, helper=helper, item=item, item_cfg=item_cfg, place=place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    place = f["place"]
    return [
        f'Write a short cautionary adventure story for a young child about a mauve {item_cfg.label} at {place.label}.',
        f"Tell a gentle story where {hero.id} wants to take {item_cfg.phrase} on an adventure, but a helper warns about danger.",
        f'Create a simple adventure tale that uses the word "mauve" and ends with a safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    item_cfg: Item = f["item_cfg"]
    place: Place = f["place"]

    qa = [
        QAItem(
            question=f"What did {hero.id} want to bring on the adventure?",
            answer=f"{hero.id} wanted to bring the {item.label}. It was mauve and special, so {hero.id} did not want to leave it behind.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {hero.id} about {place.label}?",
            answer=f"{helper.label.capitalize()} warned {hero.id} because the {item.label} might {item_cfg.issue} at {place.label}. The place was risky for that treasure.",
        ),
        QAItem(
            question=f"What did {hero.id} do after hearing the warning?",
            answer=f"{hero.id} listened and chose the safer plan. That way, the adventure could still happen without hurting the {item.label}.",
        ),
        QAItem(
            question=f"What color was the special treasure?",
            answer=f"It was mauve. The mauve color helped the treasure feel bright and memorable in the story.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does cautious mean?",
        answer="Cautious means being careful and thinking about danger before you act.",
    ),
    QAItem(
        question="What is an adventure?",
        answer="An adventure is an exciting trip or experience where something new happens.",
    ),
    QAItem(
        question="Why do people listen to warnings?",
        answer="People listen to warnings so they can avoid trouble and stay safe.",
    ),
    QAItem(
        question="What is the color mauve?",
        answer="Mauve is a soft purple color, like a dusty pinkish violet.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A place is risky or safe.
risky_place(wharf).
risky_place(cave).
risky_place(forest).
risky_place(hill).
safe_place(garden).

% Items carry features relevant to the cautionary adventure.
item(mauve_map). item(mauve_kite). item(mauve_lantern). item(mauve_shell).
mauve(mauve_map). mauve(mauve_kite). mauve(mauve_lantern). mauve(mauve_shell).

fragile(mauve_map). fragile(mauve_lantern). fragile(mauve_shell).
can_blow_away(mauve_kite).
can_tear(mauve_map).
can_crack(mauve_lantern).
can_get_lost(mauve_shell).

risky_for(mauve_map,cave).
risky_for(mauve_kite,hill).
risky_for(mauve_lantern,wharf).
risky_for(mauve_shell,forest).

valid_story(P,I) :- risky_place(P), item(I), risky_for(I,P).
valid_story(P,I) :- safe_place(P), item(I), risky_for(I,_).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].risky:
            lines.append(asp.fact("risky_place", pid))
        else:
            lines.append(asp.fact("safe_place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("mauve", iid))
        if item.fragile:
            lines.append(asp.fact("fragile", iid))
        if item.issue == "could blow away":
            lines.append(asp.fact("can_blow_away", iid))
        if item.issue == "could tear or smudge":
            lines.append(asp.fact("can_tear", iid))
        if item.issue == "could crack on the boards":
            lines.append(asp.fact("can_crack", iid))
        if item.issue == "could get lost in the leaves":
            lines.append(asp.fact("can_get_lost", iid))
        lines.append(asp.fact("risky_for", iid, item.risky_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if py - asp_set:
        print("  only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            if story_is_reasonable(place, item):
                combos.append((pid, iid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary adventure story world with a mauve treasure.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.item:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        if not story_is_reasonable(place, item):
            raise StoryError(explain_rejection(place, item))

    combos = [
        (p, i) for (p, i) in valid_combos()
        if (args.place is None or p == args.place)
        and (args.item is None or i == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item = rng.choice(sorted(combos))
    item_cfg = ITEMS[item]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.brittle:
            bits.append("brittle=True")
        if e.loss_risk:
            bits.append("loss_risk=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(place="hill", item="mauve_kite", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="wharf", item="mauve_lantern", name="Leo", gender="boy", helper="father", trait="brave"),
    StoryParams(place="cave", item="mauve_map", name="Nora", gender="girl", helper="grandma", trait="eager"),
    StoryParams(place="forest", item="mauve_shell", name="Finn", gender="boy", helper="grandpa", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for place, item in combos:
            print(f"  {place:8} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
