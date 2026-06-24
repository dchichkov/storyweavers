#!/usr/bin/env python3
"""
storyworlds/worlds/fellow_ship_paw_rosemary_happy_ending_humor.py
==================================================================

A tiny pirate-tale storyworld about a fellow-ship on the sea, a curious paw,
and a rosemary sprig that helps turn a silly problem into a happy ending.

Seed-inspired tale:
---
On a windy afternoon, Captain Pippa and her little fellow-ship sailed the
Harbor Splash, a round-bottomed boat with a squeaky paw-shaped bell. Their
friend Miso the cat kept batting at everything with a muddy paw, and that made
the deck slippery and the sailor hats funny.

Pippa had promised to bring rosemary for supper. But the rosemary sprigs kept
tumbling into the wet deck bucket, and Miso kept sneezing at the sharp smell.
The crew laughed, but they also needed the herbs to stay dry.

So Pippa tied the rosemary into a little cloth pouch and hung it from the mast,
out of paw reach. Miso got a fish biscuit, the deck got swept clean, and the
fellow-ship sailed home laughing, with supper smelling good and the rosemary
safe.

World model idea:
---
- The ship has a wet deck and a hanging herb pouch.
- The cat's paw can splat the deck and knock things over.
- Rosemary is valuable for supper and can be kept dry with a simple fix.
- The story turns from comic chaos to a clever, safe ending.

This script keeps the domain small, concrete, and state-driven, with a happy,
humorous pirate-tale tone.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class CrewKind:
    id: str
    ship_name: str
    deck_name: str
    crew_name: str
    banner: str
    home_port: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    name: str
    mess: str
    risk: str
    joke: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    name: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
    crew: str
    trouble: str
    fix: str
    captain_name: str
    paw_name: str
    seed: Optional[int] = None


CREWS = {
    "fellow_ship": CrewKind(
        id="fellow_ship",
        ship_name="the Harbor Splash",
        deck_name="the deck",
        crew_name="the fellow-ship",
        banner="a bright blue banner with a smiling fish",
        home_port="the little harbor",
        tags={"ship", "crew", "pirate"},
    ),
    "reef_crew": CrewKind(
        id="reef_crew",
        ship_name="the Reef Sprout",
        deck_name="the deck",
        crew_name="the reef-crew",
        banner="a green banner with a shell and star",
        home_port="the reef dock",
        tags={"ship", "crew", "pirate"},
    ),
}

TROUBLES = {
    "slip": Trouble(
        id="slip",
        name="a slippery deck",
        mess="wet pawprints",
        risk="someone might slide into a bucket",
        joke="the floor looked like it had learned to dance",
        tags={"wet", "deck"},
    ),
    "herbs": Trouble(
        id="herbs",
        name="the rosemary slipping away",
        mess="soggy rosemary",
        risk="the supper herbs might get damp and sad",
        joke="the sprigs kept trying to dive like tiny green pirates",
        tags={"rosemary", "herb"},
    ),
}

FIXES = {
    "pouch": Fix(
        id="pouch",
        name="a cloth pouch tied to the mast",
        method="hang the rosemary high and dry",
        result="kept the rosemary safe and smelled lovely",
        tags={"rosemary", "safe"},
    ),
    "basket": Fix(
        id="basket",
        name="a little basket with a lid",
        method="tuck the rosemary into a lid-covered basket",
        result="kept the rosemary dry and out of reach",
        tags={"rosemary", "safe"},
    ),
}

NAMES = ["Pippa", "Mina", "Lola", "Nell", "Ruby", "Tess", "Milo", "Finn", "Otto", "Jasper"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(c, t, f) for c in CREWS for t in TROUBLES for f in FIXES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about a fellow-ship, a paw, and rosemary.")
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.crew is None or c[0] == args.crew)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    crew, trouble, fix = rng.choice(sorted(combos))
    return StoryParams(
        crew=crew,
        trouble=trouble,
        fix=fix,
        captain_name=rng.choice(NAMES),
        paw_name=rng.choice([n for n in NAMES if n != rng.choice(NAMES)]),
    )


def reason_gate(params: StoryParams) -> None:
    if params.trouble == "slip" and params.fix not in {"pouch", "basket"}:
        raise StoryError("That fix does not solve the slippery deck.")
    if params.trouble == "herbs" and params.fix not in {"pouch", "basket"}:
        raise StoryError("That fix does not protect the rosemary.")


def tell(crew: CrewKind, trouble: Trouble, fix: Fix, captain_name: str, paw_name: str) -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type="girl", label=captain_name,
                               meters={"calm": 0.0}, memes={"joy": 0.0}))
    paw = world.add(Entity(id=paw_name, kind="character", type="cat", label=paw_name,
                           attrs={"paw": True}, meters={"wet": 0.0}, memes={"mischief": 0.0}))
    ship = world.add(Entity(id="ship", kind="place", type="ship", label=crew.ship_name,
                            meters={"wet": 0.0, "safety": 0.0}, memes={"humor": 0.0}))
    rosemary = world.add(Entity(id="rosemary", kind="thing", type="herb", label="rosemary",
                                attrs={"dry": True}, tags={"rosemary"}, meters={"wet": 0.0},
                                memes={"value": 1.0}))
    world.facts.update(crew=crew, trouble=trouble, fix=fix, captain=captain, paw=paw, ship=ship, rosemary=rosemary)

    world.say(f"Captain {captain_name} led the {crew.crew_name} aboard {crew.ship_name}, where {crew.banner} fluttered.")
    world.say(f"The little ship was heading home from {crew.home_port}, and the {crew.deck_name} already smelled of salt and jokes.")

    world.para()
    world.say(f"Then {paw_name} the cat waved a muddy paw and made {trouble.joke}.")
    if trouble.id == "slip":
        paw.meters["wet"] += 1
        ship.meters["wet"] += 1
        world.say(f"Every step left {trouble.mess}, and {trouble.risk}.")
    else:
        rosemary.meters["wet"] += 1
        rosemary.attrs["dry"] = False
        world.say(f"The rosemary rolled toward a puddle, and {trouble.risk}.")

    world.para()
    captain.memes["joy"] += 1
    captain.say = "none"
    world.say(f'Captain {captain_name} laughed. "That paw is a one-cat storm," {captain_name} said.')
    world.say(f'But then {captain_name} chose a clever fix: {fix.name}.')
    rosemary.attrs["dry"] = True
    rosemary.meters["wet"] = 0.0
    ship.meters["safety"] += 1
    captain.meters["calm"] += 1
    paw.memes["mischief"] += 1

    world.para()
    world.say(f"They used {fix.method}, so the rosemary {fix.result}.")
    world.say(f"{paw_name} got a fish biscuit instead of another chance to wave that ridiculous paw.")
    world.say(f'By sunset, the {crew.crew_name} sailed on with a clean deck, dry rosemary, and a very proud grin.')

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crew, trouble, fix = f["crew"], f["trouble"], f["fix"]
    return [
        f'Write a short pirate-style story for a small child about {crew.crew_name}, a silly paw, and rosemary.',
        f'Tell a funny happy-ending story where a cat paw makes trouble on {crew.ship_name} and the crew saves the rosemary.',
        f'Write a gentle story with humor where {fix.name} helps the fellow-ship keep rosemary dry on a pirate boat.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain, paw, crew, trouble, fix = f["captain"], f["paw"], f["crew"], f["trouble"], f["fix"]
    return [
        QAItem(
            question=f"Who sailed with the fellow-ship on {crew.ship_name}?",
            answer=f"Captain {captain.id} sailed with {paw.id} the cat and the rest of the {crew.crew_name}.",
        ),
        QAItem(
            question="What made the deck silly and slippery?",
            answer=f"{paw.id} waved a muddy paw, and that left {trouble.mess} on the deck.",
        ),
        QAItem(
            question="Why was rosemary important in the story?",
            answer="The rosemary was for supper, so the crew wanted to keep it dry and safe.",
        ),
        QAItem(
            question="How did the crew solve the problem?",
            answer=f"They used {fix.name} to keep the rosemary dry and out of paw reach.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a paw?",
            answer="A paw is an animal foot, like a cat's foot. Cats use their paws to walk, bat, and play.",
        ),
        QAItem(
            question="What is rosemary?",
            answer="Rosemary is a fragrant green herb that people can use to flavor food.",
        ),
        QAItem(
            question="What is a fellow-ship?",
            answer="A fellow-ship is a cheerful crew of companions who sail or work together like a team.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs} tags={sorted(e.tags)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


def generate(params: StoryParams) -> StorySample:
    reason_gate(params)
    crew = CREWS[params.crew]
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    world = tell(crew, trouble, fix, params.captain_name, params.paw_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(C,T,F) :- crew(C), trouble(T), fix(F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    out = []
    for c in CREWS:
        out.append(asp.fact("crew", c))
    for t in TROUBLES:
        out.append(asp.fact("trouble", t))
    for f in FIXES:
        out.append(asp.fact("fix", f))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    aspv = set(asp_valid_combos())
    if py != aspv:
        print("MISMATCH")
        print("python only:", sorted(py - aspv))
        print("asp only:", sorted(aspv - py))
        return 1
    sample = generate(resolve_params(argparse.Namespace(crew=None, trouble=None, fix=None), random.Random(1)))
    _ = sample.story
    print(f"OK: {len(py)} combos and story generation works.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        print(asp_program("#show valid/3."))
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for crew, trouble, fix in valid_combos():
            samples.append(generate(StoryParams(crew=crew, trouble=trouble, fix=fix, captain_name="Pippa", paw_name="Miso")))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
