#!/usr/bin/env python3
"""
Storyworld: terrier_fiat_foreshadowing_fable

A small fable-like story domain about a terrier, a sudden fiat, and a
foreshadowed choice that changes the ending. The world is intentionally tiny:
one animal, one authority figure, one decree, one object of desire, and one
simple consequence loop.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
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
        if self.type in {"terrier", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mayor", "judge", "queen", "king", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village green"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    ruler_name: str
    treasure: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "green": Setting(place="the village green", affords={"gather", "listen"}),
    "market": Setting(place="the market square", affords={"gather", "listen"}),
    "lane": Setting(place="the narrow lane", affords={"listen", "run"}),
}

TREASURES = {
    "bone": Entity(id="bone", kind="thing", label="bone", type="bone"),
    "pie": Entity(id="pie", kind="thing", label="berry pie", type="pie"),
    "bell": Entity(id="bell", kind="thing", label="little bell", type="bell"),
}

GOBLINS = [
    ("Mayor Vale", "mayor"),
    ("Queen Bria", "queen"),
    ("Judge Noll", "judge"),
]

HEROES = ["Pip", "Rufus", "Toby", "Milo", "Bram", "Scout"]
PLACES = list(SETTINGS)


# ---------------------------------------------------------------------------
# World state and narration
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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


# ---------------------------------------------------------------------------
# Tiny causal mechanics
# ---------------------------------------------------------------------------

def foreshadow(world: World, hero: Entity, ruler: Entity, treasure: Entity) -> None:
    world.say(
        f"{hero.id} was a small terrier with quick paws and a nose that noticed everything."
    )
    world.say(
        f"At {world.setting.place}, {hero.id} loved to carry away shiny things, "
        f"but {ruler.id} had a habit of speaking in sudden fiat."
    )
    world.say(
        f"One morning, {hero.id} saw {treasure.label} on a low stone and felt a warning tug in {hero.pronoun('possessive')} chest."
    )


def issue_fiat(world: World, ruler: Entity, hero: Entity, treasure: Entity) -> None:
    world.facts["fiat"] = True
    world.say(
        f"Then {ruler.id} gave a fiat: \"No one may touch the {treasure.label} until the bell rings.\""
    )
    world.say(
        f"{hero.id} heard it, and the little warning from earlier became a big one."
    )


def temptation(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    world.facts["temptation"] = True
    world.say(
        f"The {treasure.label} gleamed in the sun, and {hero.id} took one careful step closer."
    )


def choice(world: World, hero: Entity, ruler: Entity, treasure: Entity) -> None:
    obey = world.facts.get("fiat", False) and hero.memes.get("want", 0.0) >= 1.0
    if obey:
        world.say(
            f"Then {hero.id} sat down instead of snatching it, because {hero.pronoun('subject')} remembered the fiat."
        )
        world.say(
            f"{hero.id} waited with a patient nose and a still tail, and the waiting turned out to be wise."
        )
        world.facts["resolved"] = "obedience"
    else:
        hero.meters["trouble"] = hero.meters.get("trouble", 0.0) + 1.0
        world.say(
            f"{hero.id} ignored the warning and grabbed the {treasure.label}, but the bells of the village rang before {hero.pronoun('subject')} could run."
        )
        world.say(
            f"{ruler.id} frowned, and the terrier learned that a rushed paw can lead a dog into trouble."
        )
        world.facts["resolved"] = "trouble"


def ending(world: World, hero: Entity, ruler: Entity, treasure: Entity) -> None:
    if world.facts.get("resolved") == "obedience":
        world.say(
            f"When the bell finally rang, {ruler.id} smiled, and {hero.id} was praised for a wise heart."
        )
        world.say(
            f"The {treasure.label} stayed safe, and {hero.id} went home with a calm tail and a better lesson."
        )
    else:
        world.say(
            f"In the end, the {treasure.label} went back to the stone, and {hero.id} had to sit beside {ruler.id} and listen."
        )
        world.say(
            f"The terrier's ears drooped, but the village learned why a warning should be heeded before the fiat is tested."
        )


# ---------------------------------------------------------------------------
# Story build
# ---------------------------------------------------------------------------

def tell(setting: Setting, hero_name: str, ruler_name: str, treasure_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="terrier"))
    ruler = world.add(Entity(id=ruler_name, kind="character", type="queen"))
    treasure = world.add(Entity(id=treasure_name, kind="thing", label=treasure_name, type=treasure_name))

    foreshadow(world, hero, ruler, treasure)
    world.para()
    issue_fiat(world, ruler, hero, treasure)
    temptation(world, hero, treasure)
    choice(world, hero, ruler, treasure)
    world.para()
    ending(world, hero, ruler, treasure)

    world.facts.update(hero=hero, ruler=ruler, treasure=treasure, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Content selection
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "listen" in setting.affords:
            for t in TREASURES:
                combos.append((place, t))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.treasure and args.treasure not in TREASURES:
        raise StoryError("Unknown treasure.")

    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.treasure:
        combos = [c for c in combos if c[1] == args.treasure]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, treasure = rng.choice(sorted(combos))
    hero_name = args.hero or rng.choice(HEROES)
    ruler_name = args.ruler or rng.choice([n for n, _ in GOBLINS])
    return StoryParams(place=place, hero_name=hero_name, ruler_name=ruler_name, treasure=treasure)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    ruler: Entity = f["ruler"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    return [
        f'Write a short fable about a terrier named {hero.id}, a sudden fiat, and {world.setting.place}.',
        f"Tell a gentle story where {ruler.id} gives a fiat, {hero.id} wants {treasure.label}, and the choice is tested.",
        f"Write a simple animal fable that begins with a warning and ends with a lesson about listening before acting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    ruler: Entity = f["ruler"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a small terrier, and {ruler.id}, who gave the fiat at {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the fiat about?",
            answer=f"The fiat said that no one could touch the {treasure.label} until the bell rang.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to grab the {treasure.label}, but the earlier warning made the choice feel risky.",
        ),
    ]
    if f.get("resolved") == "obedience":
        qa.append(QAItem(
            question=f"How did {hero.id} handle the fiat in the end?",
            answer=f"{hero.id} listened, sat down, and waited until it was safe.",
        ))
    else:
        qa.append(QAItem(
            question=f"What happened when {hero.id} did not listen?",
            answer=f"{hero.id} got into trouble and had to give back the {treasure.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a terrier?",
            answer="A terrier is a small, lively dog that often likes to dig, chase, and investigate little things.",
        ),
        QAItem(
            question="What is a fiat?",
            answer="A fiat is a firm command or decision made by someone in charge.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints at what may happen later in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(green). place(market). place(lane).
affords(green,listen). affords(green,gather).
affords(market,listen). affords(market,gather).
affords(lane,listen). affords(lane,run).

treasure(bone). treasure(pie). treasure(bell).

valid(Place,Treasure) :- affords(Place,listen), treasure(Treasure).
foreshadowing(Place,Treasure) :- valid(Place,Treasure).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about a terrier, a fiat, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero")
    ap.add_argument("--ruler")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="green", hero_name="Pip", ruler_name="Queen Bria", treasure="bone"),
    StoryParams(place="market", hero_name="Rufus", ruler_name="Mayor Vale", treasure="bell"),
    StoryParams(place="lane", hero_name="Toby", ruler_name="Judge Noll", treasure="pie"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero_name, params.ruler_name, params.treasure)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, treasure) combos:\n")
        for place, treasure in combos:
            print(f"  {place:8} {treasure}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.treasure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
