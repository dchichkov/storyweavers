#!/usr/bin/env python3
"""
A standalone story world for an adventure-style mystery about a dishonest dictate.

Premise:
- A young explorer follows a treasure map to a small place with a locked puzzle.
- Someone has been handing out false instructions and trying to dictate the route.
- The hero must notice the dishonest clues, test them, and solve the mystery.
- The ending proves the truth by revealing the real path and the recovered object.

The world is intentionally small and constraint-driven:
- One place, one problem, one false guide, one real solution.
- Physical state tracks items, clues, and whether a path is blocked.
- Emotional state tracks worry, confidence, and the relief of solving the mystery.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    opened: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    mood: str
    has: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guide: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_reveal(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    clue = world.get("clue")
    if hero.meters.get("noticed", 0) < THRESHOLD:
        return out
    if clue.hidden:
        sig = ("reveal", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        clue.hidden = False
        out.append("A hidden clue was revealed.")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    prize = world.get("prize")
    guide = world.get("guide")
    clue = world.get("clue")
    if hero.meters.get("tested", 0) < THRESHOLD:
        return out
    if guide.meters.get("dishonest", 0) < THRESHOLD:
        return out
    if clue.hidden:
        return out
    sig = ("solve", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.opened = True
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    out.append("The mystery was solved.")
    return out


def _r_confidence(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    prize = world.get("prize")
    if prize.opened and hero.memes.get("relief", 0) >= THRESHOLD:
        sig = ("confidence", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
        out.append("The hero felt brave again.")
    return out


RULES = [_r_reveal, _r_solve, _r_confidence]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            before = len(produced)
            produced.extend(rule(world))
            if len(produced) != before:
                changed = True
    if narrate:
        for s in produced:
            world.say(s)


def describe_place(place: Place) -> str:
    if place.name == "jungle camp":
        return "The jungle camp was warm, green, and full of rustling leaves."
    if place.name == "old tower":
        return "The old tower leaned over the path like a giant listening for secrets."
    return f"{place.name.capitalize()} looked quiet, with adventure hiding in every corner."


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    guide = world.add(Entity(id="guide", kind="character", type="fox", label=params.guide))
    clue = world.add(Entity(id="clue", type="note", label="clue", hidden=True))
    prize = world.add(Entity(id="prize", type="box", label=params.prize))
    path = world.add(Entity(id="path", type="path", label="path"))
    key = world.add(Entity(id="key", type="key", label="small key", carried_by="guide"))
    guide.meters["dishonest"] = 1
    world.facts.update(hero=hero, guide=guide, clue=clue, prize=prize, path=path, key=key)
    return world


def intro(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    world.say(
        f"{hero.label} was a little {hero.type} who loved adventure and mystery."
    )
    world.say(
        f"At the camp, {guide.label} kept trying to dictate the plan with a smile that did not feel honest."
    )
    world.say(describe_place(world.place))


def setup_mystery(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    prize = world.get("prize")
    clue = world.get("clue")
    world.say(
        f"Someone had hidden {prize.label} near the old trail, and a crooked sign pointed the wrong way."
    )
    world.say(
        f"{guide.label} said the map was simple, but {hero.label} noticed that the directions sounded dishonest."
    )
    hero.memes["worry"] = 1
    clue.meters["important"] = 1


def test_clue(world: World) -> None:
    hero = world.get("hero")
    clue = world.get("clue")
    guide = world.get("guide")
    hero.meters["noticed"] = 1
    world.say(
        f"{hero.label} bent down and checked the bark, the stones, and the trail marks."
    )
    world.say(
        f"Under a leaf, {hero.label} found a tiny clue that did not match {guide.label}'s story."
    )
    propagate(world, narrate=True)
    hero.meters["tested"] = 1
    world.say(
        f"That meant the guide had tried to dictate the route with false words, but the real trail was nearby."
    )


def solve_and_return(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    prize = world.get("prize")
    key = world.get("key")
    world.say(
        f"{hero.label} followed the small prints, found the key, and opened the box."
    )
    prize.opened = True
    propagate(world, narrate=True)
    world.say(
        f"{guide.label} lowered {guide.pronoun('possessive')} ears, and {hero.label} carried the prize back to camp."
    )
    world.say(
        f"In the end, the dishonest dictate was beaten by careful looking, and the mystery was solved."
    )


PLACES = {
    "jungle camp": Place(name="jungle camp", mood="lush", has={"path", "leaf", "trail"}),
    "old tower": Place(name="old tower", mood="echoing", has={"stone", "stairs", "dust"}),
    "river bend": Place(name="river bend", mood="bright", has={"water", "reeds", "mud"}),
}

PRIZES = {
    "golden box": "golden box",
    "silver compass": "silver compass",
    "lost lantern": "lost lantern",
}

HERO_NAMES = ["Milo", "Nia", "Tess", "Arin", "Sora", "Pip"]
GUIDE_NAMES = ["Fox", "Moss", "Tula", "Brindle", "Wren"]
HERO_TYPES = ["boy", "girl"]


@dataclass
class AspFacts:
    place: str
    dishonest: bool
    hidden_clue: bool
    solved: bool


ASP_RULES = r"""
dishonest_guide(G) :- guide(G), dishonest(G).
clue_hidden(C) :- clue(C), hidden(C).
clue_revealed(C) :- clue(C), not hidden(C).
mystery_solved(P) :- prize(P), clue_revealed(_), dishonest_guide(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for name in HERO_NAMES:
        lines.append(asp.fact("name", name))
    for g in GUIDE_NAMES:
        lines.append(asp.fact("guide", g))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/1."))
    atoms = set(asp.atoms(model, "mystery_solved"))
    if atoms == set():
        print("OK: ASP program is present and deterministic for the base facts.")
        return 0
    print("Unexpected ASP output:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure mystery story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--guide", choices=GUIDE_NAMES)
    ap.add_argument("--prize", choices=PRIZES)
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
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.gender or rng.choice(HERO_TYPES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    prize = args.prize or rng.choice(list(PRIZES))
    if hero_name == guide:
        raise StoryError("The hero and the guide must be different characters.")
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, guide=guide, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    intro(world)
    world.para()
    setup_mystery(world)
    world.para()
    test_clue(world)
    world.para()
    solve_and_return(world)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write an adventure story where {p.hero_name} notices a dishonest guide and solves a mystery.",
        f"Tell a child-friendly tale about a {p.hero_type} named {p.hero_name} who must ignore false directions and find the real clue.",
        f"Create a short adventure with a hidden object, a dishonest dictate, and a solved mystery at {p.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.get("hero")
    guide = world.get("guide")
    prize = world.get("prize")
    return [
        QAItem(
            question=f"Who was trying to dictate the route?",
            answer=f"{guide.label} was trying to dictate the route, but the directions were dishonest."
        ),
        QAItem(
            question=f"What did {hero.label} have to do to solve the mystery?",
            answer=f"{hero.label} had to notice the clue, test the trail, and follow the real signs instead of the false ones."
        ),
        QAItem(
            question=f"What did {hero.label} find at the end?",
            answer=f"{hero.label} found and recovered the {prize.label}, which proved the mystery was solved."
        ),
        QAItem(
            question=f"Why did the hero not trust the first directions?",
            answer=f"The first directions sounded dishonest, so {hero.label} looked more carefully before following them."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    place = world.place
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling problem that needs careful thinking and clues to solve."
        ),
        QAItem(
            question="What does dishonest mean?",
            answer="Dishonest means not telling the truth or trying to trick someone."
        ),
        QAItem(
            question="What does dictate mean?",
            answer="To dictate means to tell someone what to do or what words to write, sometimes in a bossy way."
        ),
        QAItem(
            question=f"What kind of place is {place.name}?",
            answer=f"{place.name.capitalize()} is a {place.mood} place for an adventure."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.opened:
            bits.append("opened=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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
    lines.append("== (3) World knowledge questions ==")
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
    StoryParams(place="jungle camp", hero_name="Milo", hero_type="boy", guide="Fox", prize="golden box"),
    StoryParams(place="old tower", hero_name="Nia", hero_type="girl", guide="Brindle", prize="silver compass"),
    StoryParams(place="river bend", hero_name="Tess", hero_type="girl", guide="Moss", prize="lost lantern"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1. #show guide/1. #show prize/1."))
    return sorted(set(asp.atoms(model, "place")) | set(asp.atoms(model, "guide")) | set(asp.atoms(model, "prize")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery_solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show mystery_solved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero_name} at {p.place} with {p.guide} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
