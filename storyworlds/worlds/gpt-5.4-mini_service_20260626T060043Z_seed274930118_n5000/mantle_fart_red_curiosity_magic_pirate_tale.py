#!/usr/bin/env python3
"""
A standalone story world: a small Pirate Tale about curiosity, magic, and a
very odd red mantle that lets a careful pirate solve a stinky problem.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: str


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "deck": Setting(place="the moonlit deck", afford="breeze"),
    "harbor": Setting(place="the red harbor", afford="breeze"),
    "cove": Setting(place="the quiet cove", afford="breeze"),
}

HEROES = ["Mira", "Jory", "Nell", "Pip", "Rosa", "Tobin", "Sailor Finn"]
COMPANIONS = ["first mate", "old parrot", "small deckhand", "tiny lantern"]
TRAITS = ["curious", "bold", "cheerful", "quick-witted"]


@dataclass
class StoryConfig:
    place: str
    hero: str
    hero_type: str
    companion: str


ASP_RULES = r"""
hero(H). companion(C). place(P). mantle(M). red(M) :- red_mantle(M).
curious(H) :- has_memes(H,curiosity).
magic(Mg) :- has_memes(Mg,magic).

problem(P) :- fart_event(F), stinks(F), place(P).
helpful(M) :- mantle(M), red(M), magical(M).
safe(H) :- wears(H,M), helpful(M), fart_event(F), stinks(F), shielded(H,F).

story_ok :- hero(H), place(P), mantle(M), curious(H), magic(Mg), helpful(M).
#show story_ok/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
    for h in HEROES:
        lines.append(asp.fact("hero_name", h))
    for c in COMPANIONS:
        lines.append(asp.fact("companion_name", c))
    lines.append(asp.fact("red_mantle", "mantle"))
    lines.append(asp.fact("magical", "mantle"))
    lines.append(asp.fact("fart_event", "fart"))
    lines.append(asp.fact("stinks", "fart"))
    lines.append(asp.fact("has_memes", "hero", "curiosity"))
    lines.append(asp.fact("has_memes", "magic", "magic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP twin accepts the core story world.")
        return 0
    print("MISMATCH: ASP twin rejected the core story world.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate Tale story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.name or rng.choice(HEROES)
    hero_type = "pirate"
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(place=place, hero=hero, hero_type=hero_type, companion=companion)


def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    companion = world.add(Entity(id="companion", kind="character", type="parrot", label=params.companion))
    mantle = world.add(Entity(
        id="mantle",
        type="mantle",
        label="red mantle",
        phrase="a red mantle with a strange stitched swirl",
        owner=hero.id,
        worn_by=hero.id,
        plural=False,
        meters={"red": 1.0},
        memes={"magic": 1.0},
    ))
    world.facts = {
        "hero": hero,
        "companion": companion,
        "mantle": mantle,
        "place": world.setting.place,
    }

    world.say(
        f"{params.hero} was a curious pirate who loved every mystery on the ship."
        f" {params.companion.capitalize()} was always nearby, bobbing on a rope and watching the waves."
    )
    world.say(
        f"One evening on {world.setting.place}, {params.hero} found {mantle.phrase}. "
        f"The cloth was bright red, and it shimmered like it had swallowed a tiny spell."
    )
    world.say(
        f"{params.hero} tucked the red mantle around {hero.pronoun('possessive')} shoulders and felt a spark of magic in the air."
    )

    world.para()
    world.say(
        f"Then a sneaky fart puffed up from behind a barrel and rolled across the deck."
        f" It was a rude, stinky cloud, and even the gulls flapped away."
    )
    hero.meters["stink"] = 1.0
    hero.memes["curiosity"] = 1.0
    companion.meters["stink"] = 1.0
    world.say(
        f"{params.hero} wrinkled {hero.pronoun('possessive')} nose, but curiosity made {hero.pronoun('object')} look closer."
    )
    world.say(
        f"{params.companion} squawked, \"Keep that magical red mantle close!\""
    )

    world.para()
    world.say(
        f"{params.hero} lifted the mantle high like a flag and gave it a twirl."
        f" The magic in the cloth caught the air, and the stink puff split apart before it could reach the lanterns."
    )
    hero.meters["safe"] = 1.0
    mantle.memes["magic"] = 2.0
    world.say(
        f"The deck smelled clean again. {params.hero} laughed, {params.companion} chirped, and the red mantle fluttered in the sea wind like a brave little sail."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        mantle=mantle,
        params=params,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    prompts = [
        'Write a short Pirate Tale for a child about a curious pirate, a magical red mantle, and a fart on the deck.',
        f"Tell a gentle pirate story where {params.hero} finds a red mantle and uses magic to solve a stinky problem.",
        "Write a story with the words mantle, fart, red, Curiosity, and Magic, ending with a clever rescue."
    ]
    story_qa = [
        QAItem(
            question=f"Who found the red mantle on the deck?",
            answer=f"{params.hero} found the red mantle on {world.setting.place}."
        ),
        QAItem(
            question="Why did the pirate look closer at the stinky puff?",
            answer=f"Because {params.hero} was full of curiosity and wanted to understand the strange fart cloud."
        ),
        QAItem(
            question="How did the red mantle help?",
            answer="Its magic split the stink apart and kept the pirate and the lanterns safe."
        ),
    ]
    world_qa = [
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn about something new."
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is special story power that can do surprising things that real things cannot do."
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.label, dict(e.meters), dict(e.memes))
    if qa:
        print("\n--- QA ---")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible pirate story world found.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="deck", hero="Mira", hero_type="pirate", companion="old parrot"),
            StoryParams(place="harbor", hero="Jory", hero_type="pirate", companion="first mate"),
            StoryParams(place="cove", hero="Nell", hero_type="pirate", companion="small deckhand"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
