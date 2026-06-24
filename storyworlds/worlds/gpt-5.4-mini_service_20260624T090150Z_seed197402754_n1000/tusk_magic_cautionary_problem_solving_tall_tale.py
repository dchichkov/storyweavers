#!/usr/bin/env python3
"""
A tall-tale story world about a magic tusk, a cautionary problem, and a clever fix.

Seed tale sketch:
---
In a river town where the wind could whistle like a fiddle, there lived a young
elephant named Tula. Tula found an old ivory tusk that could do one small magic
thing: whenever someone told a boast too loud, the tusk made the nearest muddy
spot grow bigger. Tula loved showing it off.

One bright afternoon, Tula bragged so hard that the muddy riverbank swelled up
and blocked the bridge. The town got stuck. Tula felt terrible. Then Tula and
Grandpa Goro thought hard, used the tusk's magic carefully, and shrank the mud
back down by speaking only true words and helping everyone work together.
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
class Place:
    name: str
    feature: str
    weather: str
    detail: str


@dataclass
class Character:
    name: str
    role: str
    trait: str


@dataclass
class Tusk:
    label: str
    material: str = "ivory"
    magic: str = "makes a muddy spot grow when someone boasts too loudly"
    caution: str = "works best when people tell the truth"
    fix: str = "shrinks the mud when used with careful words and helpful hands"


@dataclass
class World:
    place: Place
    hero: Character
    elder: Character
    tusk: Tusk
    boast_count: int = 0
    mud_level: int = 0
    bridge_blocked: bool = False
    resolved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            place=self.place,
            hero=self.hero,
            elder=self.elder,
            tusk=self.tusk,
            boast_count=self.boast_count,
            mud_level=self.mud_level,
            bridge_blocked=self.bridge_blocked,
            resolved=self.resolved,
            paragraphs=[[]],
            facts=dict(self.facts),
        )


@dataclass
class StoryParams:
    place: str
    hero: str
    elder: str
    weather: str
    seed: Optional[int] = None


PLACES = {
    "river_town": Place(
        name="River Town",
        feature="a wide river and a bridge of planks",
        weather="bright",
        detail="The river shone like a silver ribbon under the sun.",
    ),
    "hill_fair": Place(
        name="Huckle Hill Fair",
        feature="a windy fairground full of wagons and banners",
        weather="windy",
        detail="The banners snapped and danced like bright birds.",
    ),
    "banana_dock": Place(
        name="Banana Dock",
        feature="a dock beside a sleepy blue inlet",
        weather="clear",
        detail="The dock smelled of salt, wood, and sweet bananas.",
    ),
}

HEROES = [
    Character(name="Tula", role="young elephant", trait="curious"),
    Character(name="Milo", role="baby elephant", trait="lively"),
    Character(name="Nina", role="small elephant", trait="bold"),
]

ELDERS = [
    Character(name="Goro", role="grandpa", trait="wise"),
    Character(name="Mabel", role="auntie", trait="patient"),
    Character(name="Pip", role="uncle", trait="steady"),
]

TUSK = Tusk(label="magic tusk")


ASP_RULES = r"""
place(river_town). place(hill_fair). place(banana_dock).

hero(tula). hero(milo). hero(nina).
elder(goro). elder(mabel). elder(pip).

boastful(tula). boastful(milo). boastful(nina).
wise(goro). wise(mabel). wise(pip).

at_risk(P) :- place(P).
resolves(P) :- place(P), hero(H), elder(E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for h in HEROES:
        lines.append(asp.fact("hero", h.name.lower()))
        lines.append(asp.fact("trait", h.name.lower(), h.trait))
    for e in ELDERS:
        lines.append(asp.fact("elder", e.name.lower()))
        lines.append(asp.fact("trait", e.name.lower(), e.trait))
    lines.append(asp.fact("tusk", "magic_tusk"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_places() -> list[str]:
    return list(PLACES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    if place not in PLACES:
        raise StoryError("Unknown place.")
    hero = args.hero or rng.choice(HEROES).name
    elder = args.elder or rng.choice(ELDERS).name
    weather = args.weather or PLACES[place].weather
    return StoryParams(place=place, hero=hero, elder=elder, weather=weather)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = next(h for h in HEROES if h.name == params.hero)
    elder = next(e for e in ELDERS if e.name == params.elder)
    world = World(place=place, hero=hero, elder=elder, tusk=TUSK)
    world.facts.update(place=place, hero=hero, elder=elder, tusk=TUSK, weather=params.weather)

    world.say(f"Folks said {place.name} was a place where even the dust had a story to tell.")
    world.say(
        f"There lived {hero.name}, a {hero.trait} {hero.role}, and {elder.name}, "
        f"{elder.role} as steady as a fencepost."
    )
    world.say(
        f"{hero.name} found a {TUSK.material} {TUSK.label} that {TUSK.magic}, "
        f"and everybody warned that the trick was {TUSK.caution}."
    )

    world.para()
    world.say(f"One {params.weather} day, {hero.name} began to boast bigger than a barn door.")
    world.boast_count += 1
    world.mud_level += 1
    world.say(
        f"The {place.feature} listened, and the muddy bank swelled up until the bridge "
        f"was blocked by a heap of brown muck."
    )
    world.bridge_blocked = True
    world.say(
        f"That was a sorry sight, because wagons could not cross and children could not "
        f"reach the market."
    )

    world.para()
    world.say(
        f"{elder.name} did not scold. Instead, {elder.name} said, "
        f'"A magic thing needs careful hands, not show-off words."'
    )
    world.say(
        f"Together they spoke plain true words, sang a slow counting song, and used the "
        f"{TUSK.label} the right way."
    )
    world.mud_level = max(0, world.mud_level - 1)
    world.bridge_blocked = False
    world.resolved = True
    world.say(
        f"The mud shrank back to a small brown patch, the bridge cleared, and "
        f"{hero.name} promised to brag less and help more."
    )
    world.say(
        f"By supper time, {place.name} was shining again, and the {TUSK.label} lay quiet "
        f"as a moonbeam in {elder.name}'s careful hands."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short tall tale for a child about a magic tusk, a problem, and a careful fix.',
        f"Tell a cautionary story where {f['hero'].name} finds a magic tusk and learns "
        f"that boasting can cause trouble.",
        f"Write a story set in {f['place'].name} about a muddy problem that gets solved "
        f"with honest words and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    elder: Character = f["elder"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who found the magic tusk in {place.name}?",
            answer=f"{hero.name}, the {hero.trait} {hero.role}, found the magic tusk.",
        ),
        QAItem(
            question=f"What happened after {hero.name} boasted too loudly?",
            answer=(
                f"The muddy bank swelled up and blocked the bridge, so nobody could cross "
                f"until the problem was fixed."
            ),
        ),
        QAItem(
            question=f"How did {hero.name} and {elder.name} solve the trouble?",
            answer=(
                f"They used the tusk carefully, spoke true words, and worked together until "
                f"the mud shrank back down."
            ),
        ),
        QAItem(
            question=f"What did {hero.name} promise at the end?",
            answer=f"{hero.name} promised to brag less and help more.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tusk?",
            answer="A tusk is a long, pointed tooth that some animals grow outside their mouths.",
        ),
        QAItem(
            question="Why can boasting cause trouble in a cautionary story?",
            answer="Boasting can lead a character to make bad choices and ignore a careful warning.",
        ),
        QAItem(
            question="Why is teamwork helpful when a big problem blocks the way?",
            answer="Teamwork lets people combine their ideas and hands to solve the problem faster.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"  place={world.place.name!r} feature={world.place.feature!r}",
            f"  hero={world.hero.name!r} role={world.hero.role!r} trait={world.hero.trait!r}",
            f"  elder={world.elder.name!r} role={world.elder.role!r} trait={world.elder.trait!r}",
            f"  tusk={world.tusk.label!r} magic={world.tusk.magic!r}",
            f"  boast_count={world.boast_count}",
            f"  mud_level={world.mud_level}",
            f"  bridge_blocked={world.bridge_blocked}",
            f"  resolved={world.resolved}",
        ]
    )


ASP_RULES_INLINE = r"""
% Minimal declarative twin for the story-world gate.
valid_place(P) :- place(P).
valid_story(P) :- valid_place(P).
"""


def asp_verify() -> int:
    import asp
    program = f"{asp_facts()}\n{ASP_RULES_INLINE}\n#show valid_story/1.\n"
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p,) for p in valid_places()}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_places() ({len(clingo_set)} places).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a magic tusk.")
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--hero", choices=[h.name for h in HEROES])
    ap.add_argument("--elder", choices=[e.name for e in ELDERS])
    ap.add_argument("--weather", choices=["bright", "windy", "clear"])
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
    StoryParams(place="river_town", hero="Tula", elder="Goro", weather="bright"),
    StoryParams(place="hill_fair", hero="Milo", elder="Mabel", weather="windy"),
    StoryParams(place="banana_dock", hero="Nina", elder="Pip", weather="clear"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES_INLINE}\n#show valid_story/1.\n")
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.hero} at {p.place} (elder: {p.elder})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
