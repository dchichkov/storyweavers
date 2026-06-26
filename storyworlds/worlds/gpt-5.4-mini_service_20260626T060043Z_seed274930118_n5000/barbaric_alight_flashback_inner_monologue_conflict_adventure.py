#!/usr/bin/env python3
"""
A small adventure storyworld about a daring traveler, a risky path, a flashback,
an inner monologue, and a conflict that ends in a bright, hopeful turn.

Seed words: barbaric, alight
Narrative instruments: Flashback, Inner Monologue, Conflict
Style: Adventure
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
class Person:
    name: str
    role: str
    meme: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["bravery", "fear", "hope", "resolve", "hurt"]:
            self.meme.setdefault(k, 0.0)
        for k in ["distance", "light", "safe_path", "damage"]:
            self.meters.setdefault(k, 0.0)


@dataclass
class Place:
    name: str
    description: str
    danger: str
    escape: str


@dataclass
class Item:
    name: str
    kind: str
    owner: Optional[str] = None
    lit: bool = False
    useful: bool = True
    meters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["brightness", "wear", "soot"]:
            self.meters.setdefault(k, 0.0)


@dataclass
class World:
    place: Place
    hero: Person
    companion: Person
    item: Item
    relic: Item
    flashback_seen: bool = False
    conflict: bool = False
    resolved: bool = False
    lines: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.lines.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        return copy.deepcopy(self)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "ruins": Place(
        name="the old ruins",
        description="broken stone arches and a narrow stair that vanished into shadow",
        danger="a dark chasm",
        escape="a side stair by the torchlit wall",
    ),
    "cave": Place(
        name="the deep cave",
        description="cold walls, dripping water, and a long hall that echoed every step",
        danger="a sleeping stone gate",
        escape="a crack behind the mossy shelf",
    ),
    "jungle": Place(
        name="the jungle path",
        description="thick leaves, hanging roots, and a muddy track under a hot green canopy",
        danger="a rushing ravine",
        escape="a rope bridge hidden by vines",
    ),
}

HEROES = [
    ("Mara", "young scout"),
    ("Tobin", "brave runner"),
    ("Nia", "curious explorer"),
    ("Jory", "quick-footed guide"),
]

COMPANIONS = [
    ("a lantern-bearer", "companion"),
    ("an old ranger", "companion"),
    ("a small mapmaker", "companion"),
]

ITEMS = [
    Item(name="torch", kind="light"),
    Item(name="lamp", kind="light"),
]

RELICS = [
    Item(name="silver key", kind="relic"),
    Item(name="stone charm", kind="relic"),
    Item(name="ancient coin", kind="relic"),
]

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    hero_role: str
    companion_name: str
    companion_role: str
    item: str
    relic: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _lower_name(s: str) -> str:
    return s.strip()


def _article(word: str) -> str:
    return "an" if word[0].lower() in "aeiou" else "a"


def _capitalize_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    place = PLACES[params.place]
    hero = Person(name=params.hero, role=params.hero_role)
    companion = Person(name=params.companion_name, role=params.companion_role)
    item = Item(name=params.item, kind="light", owner=hero.name)
    relic = Item(name=params.relic, kind="relic", owner=hero.name)
    return World(place=place, hero=hero, companion=companion, item=item, relic=relic)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def ignite(world: World) -> None:
    world.item.lit = True
    world.item.meters["brightness"] = 1.0
    world.hero.meters["light"] += 1
    world.hero.meme["hope"] += 1
    world.say(
        f"{world.hero.name} lit the {world.item.name}, and the dark path turned alight."
    )


def flashback(world: World) -> None:
    if world.flashback_seen:
        return
    world.flashback_seen = True
    world.hero.meme["fear"] += 1
    world.hero.meme["resolve"] += 1
    world.say(
        f"For a moment, {world.hero.name} remembered a barbaric storm from long ago, "
        f"when the path had swallowed every brave sound."
    )


def inner_monologue(world: World) -> None:
    world.hero.meme["hope"] += 0.5
    world.hero.meme["fear"] += 0.5
    world.say(
        f'Inside, {world.hero.name} thought, "I can be scared and still keep going."'
    )


def conflict(world: World) -> None:
    world.conflict = True
    world.hero.meme["fear"] += 1
    world.hero.meme["resolve"] += 1
    world.hero.meters["distance"] += 1
    world.say(
        f"Then the ground opened near {world.place.danger}, and the path became a conflict "
        f"between turning back and pushing on."
    )


def push_forward(world: World) -> None:
    world.hero.meters["safe_path"] += 1
    world.companion.meme["hope"] += 1
    world.say(
        f"{world.companion.name} pointed to {world.place.escape}, and together they chose the narrow safe way."
    )


def resolve(world: World) -> None:
    world.resolved = True
    world.hero.meme["fear"] = max(0.0, world.hero.meme["fear"] - 1.0)
    world.hero.meme["hope"] += 1.0
    world.relic.owner = world.hero.name
    world.say(
        f"At last, {world.hero.name} reached the relic, held it tight, and stepped out where the torchlight made the stones glow."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    world.say(
        f"{world.hero.name}, {world.hero.role}, entered {world.place.name} with {world.companion.name} beside them."
    )
    world.say(f"The air was full of {world.place.description}.")
    ignite(world)
    flashback(world)
    inner_monologue(world)
    conflict(world)
    push_forward(world)
    resolve(world)
    world.facts = {
        "hero": world.hero,
        "companion": world.companion,
        "place": world.place,
        "item": world.item,
        "relic": world.relic,
        "conflict": world.conflict,
        "resolved": world.resolved,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write an adventure story for a young child that includes "{world.hero.name}", a lit {world.item.name}, and a hidden relic.',
        f"Tell a story with a flashback, an inner monologue, and a conflict in {world.place.name}.",
        f"Write a brave little adventure where the path turns alight and the hero keeps going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who went into {world.place.name}?",
            answer=f"{world.hero.name} went into {world.place.name} with {world.companion.name}.",
        ),
        QAItem(
            question=f"What did {world.hero.name} light?",
            answer=f"{world.hero.name} lit the {world.item.name}, and it made the path alight.",
        ),
        QAItem(
            question="What did the hero remember for a moment?",
            answer="The hero remembered a barbaric storm from long ago.",
        ),
        QAItem(
            question="How did the conflict get solved?",
            answer=f"They followed {world.place.escape} and kept going until the relic was found.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a lantern or torch for?",
        answer="A lantern or torch helps people see in the dark by giving off light.",
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is when a story briefly shows something that happened before the main moment.",
    ),
    QAItem(
        question="What does an inner monologue show?",
        answer="An inner monologue shows what a character is thinking inside their own head.",
    ),
    QAItem(
        question="What is a conflict in a story?",
        answer="A conflict is a problem or struggle that makes the characters have to decide what to do next.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(ruins). place(cave). place(jungle).
hero(mara). hero(tobin). hero(nia). hero(jory).
item(torch). item(lamp).
relic(key). relic(charm). relic(coin).

lit(X) :- item(X).
alight(X) :- lit(X).
flashback_possible :- place(ruins).
inner_monologue_possible :- hero(_).
conflict_possible :- place(_), hero(_), item(_).

valid_story(P,H,I,R) :- place(P), hero(H), item(I), relic(R).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n, _ in HEROES:
        lines.append(asp.fact("hero", n.lower()))
    for itm in ITEMS:
        lines.append(asp.fact("item", itm.name.replace(" ", "_")))
    for r in RELICS:
        lines.append(asp.fact("relic", r.name.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    found = set(asp.atoms(model, "valid_story"))
    expected = set()
    for p in PLACES:
        for h, _ in HEROES:
            for i in ITEMS:
                for r in RELICS:
                    expected.add((p, h.lower(), i.name.replace(" ", "_"), r.name.replace(" ", "_")))
    if found == expected:
        print(f"OK: ASP parity matches ({len(found)} combinations).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("only in ASP:", sorted(found - expected))
    print("only in Python:", sorted(expected - found))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero_name, hero_role = args.hero or rng.choice(HEROES)
    companion_name, companion_role = args.companion or rng.choice(COMPANIONS)
    item = args.item or rng.choice([i.name for i in ITEMS])
    relic = args.relic or rng.choice([r.name for r in RELICS])
    if args.item and args.item not in [i.name for i in ITEMS]:
        raise StoryError("Unknown item.")
    if args.relic and args.relic not in [r.name for r in RELICS]:
        raise StoryError("Unknown relic.")
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    return StoryParams(
        place=place,
        hero=_lower_name(hero_name),
        hero_role=hero_role,
        companion_name=_lower_name(companion_name),
        companion_role=companion_role,
        item=item,
        relic=relic,
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
        print()
        print("--- trace ---")
        print(f"hero fear={sample.world.hero.meme['fear']}, hope={sample.world.hero.meme['hope']}, resolve={sample.world.hero.meme['resolve']}")
        print(f"conflict={sample.world.conflict}, resolved={sample.world.resolved}")
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with flashback, inner monologue, and conflict.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--hero", nargs=2, metavar=("NAME", "ROLE"))
    ap.add_argument("--companion", nargs=2, metavar=("NAME", "ROLE"))
    ap.add_argument("--item", choices=[i.name for i in ITEMS])
    ap.add_argument("--relic", choices=[r.name for r in RELICS])
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


CURATED = [
    StoryParams(place="ruins", hero="Mara", hero_role="young scout", companion_name="the old ranger", companion_role="companion", item="torch", relic="silver key"),
    StoryParams(place="cave", hero="Tobin", hero_role="brave runner", companion_name="a lantern-bearer", companion_role="companion", item="lamp", relic="stone charm"),
    StoryParams(place="jungle", hero="Nia", hero_role="curious explorer", companion_name="a small mapmaker", companion_role="companion", item="torch", relic="ancient coin"),
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
        model = asp.one_model(asp_program("#show valid_story/4."))
        for atom in sorted(set(asp.atoms(model, "valid_story"))):
            print(atom)
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
            params.seed = base_seed + i
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
            header = f"### {p.hero} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
