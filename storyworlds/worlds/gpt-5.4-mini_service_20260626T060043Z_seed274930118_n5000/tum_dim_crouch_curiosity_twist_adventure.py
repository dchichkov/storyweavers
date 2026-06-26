#!/usr/bin/env python3
"""
A small storyworld about curiosity, a twist, and a dim little tunnel adventure.

The seed suggests a scene close to an adventure tale:
- a child is curious
- a path is tum-dim / dim-tunnel-like
- the child must crouch to get through
- a twist changes the plan and reveals a safer, brighter way
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    dim: bool
    kind: str
    has_twist: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guide_name: str
    guide_type: str
    path: str
    prize: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "cave": Place(id="cave", label="the tum-dim cave", dim=True, kind="cave", has_twist=True, affords={"crawl", "explore"}),
    "tunnel": Place(id="tunnel", label="the tum-dim tunnel", dim=True, kind="tunnel", has_twist=True, affords={"crawl", "explore"}),
    "ruins": Place(id="ruins", label="the old ruins", dim=True, kind="ruins", has_twist=True, affords={"explore"}),
    "garden_path": Place(id="garden_path", label="the garden path", dim=False, kind="path", has_twist=False, affords={"explore"}),
}

PRIZES = {
    "map": ("a folded paper map", "map"),
    "lantern": ("a small lantern", "lantern"),
    "key": ("a brass key", "key"),
    "shell": ("a shiny shell", "shell"),
}

GEAR = {
    "kneepads": Gear(id="kneepads", label="kneepads", phrase="soft kneepads", helps={"crawl"}, covers={"knees"}),
    "lantern": Gear(id="lantern_gear", label="lantern", phrase="a bright lantern", helps={"explore", "crawl"}, covers={"hands"}),
    "boots": Gear(id="boots", label="boots", phrase="sturdy boots", helps={"explore"}, covers={"feet"}),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nina", "Ivy", "Maya"]
BOY_NAMES = ["Evan", "Owen", "Milo", "Finn", "Theo", "Luca"]
GUIDE_NAMES = ["Grandma", "Uncle", "Aunt", "Dad", "Mom", "Sister"]
TRAITS = ["curious", "brave", "gentle", "quick", "patient"]


def reasonableness_gate(place: Place, prize: str) -> bool:
    return place.has_twist and prize in {"map", "lantern", "key", "shell"}


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dim:
            lines.append(asp.fact("dim", pid))
        if p.has_twist:
            lines.append(asp.fact("twisty", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for gid, (phrase, _) in PRIZES.items():
        lines.append(asp.fact("prize", gid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


ASP_RULES = r"""
eligible(P, Prize) :- twisty(P), prize(Prize).
shown(Prize) :- prize(Prize).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny adventure storyworld with curiosity and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--path", choices=["crawl", "explore"])
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
    prize = args.prize or rng.choice(list(PRIZES))
    p = PLACES[place]
    if not reasonableness_gate(p, prize):
        raise StoryError("This adventure needs a dim, twisty place and a small prize worth seeking.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    guide_type = "mother" if guide == "Mom" else "father" if guide == "Dad" else "guide"
    path = args.path or rng.choice(sorted(p.affords))
    if path not in p.affords:
        raise StoryError("That path does not fit the chosen place.")
    return StoryParams(place=place, hero_name=name, hero_type=gender, guide_name=guide, guide_type=guide_type, path=path, prize=prize)


def _do_path(world: World, hero: Entity, guide: Entity, prize: Entity, narrate: bool = True) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    if world.place.dim:
        hero.meters["careful_steps"] = hero.meters.get("careful_steps", 0) + 1
        world.say(f"The {world.place.label} was tum-dim, so {hero.id} had to crouch to move ahead.")
    else:
        world.say(f"{hero.id} walked straight along {world.place.label}.")
    if world.place.has_twist:
        hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
        world.say(f"Then a twist in the path opened a hidden side-way, and the little lantern light found it.")
    if prize.worn_by is None:
        prize.meters["found"] = 1
        prize.owner = hero.id
        world.say(f"Near the turn, {hero.id} found {prize.phrase}.")
    if narrate and guide:
        world.say(f"{guide.id} smiled and stayed close, ready to help if the way got tricky.")


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    prize_label, prize_type = PRIZES[params.prize]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    guide = world.add(Entity(id=params.guide_name, kind="character", type=params.guide_type, label=params.guide_name))
    prize = world.add(Entity(id="prize", type=prize_type, label=prize_type, phrase=prize_label, owner=hero.id))
    gear = world.add(Entity(id="gear", type="gear", label="lantern", phrase="a bright lantern"))

    hero.memes["curiosity"] = 1
    world.say(f"{hero.id} was a {random.choice(TRAITS)} little {hero.type} who loved curiosity and adventure.")
    world.say(f"One day, {hero.id} and {guide.id} went to {world.place.label} to look for {prize.phrase}.")
    world.para()
    world.say(f"{hero.id} wanted to {params.path} into the dark part first, because the unknown felt exciting.")
    world.say(f"{guide.id} warned that the way was tum-dim, and that a careful crouch would be needed.")
    world.para()
    _do_path(world, hero, guide, prize)
    if world.place.has_twist:
        world.say(f"At the twist, the hidden bend turned the search into a new adventure, and the lantern made the dark friendly.")
    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"At last, {hero.id} held {prize.phrase} up high. The crouch, the twist, and the dim path had led to a bright find.")
    world.facts.update(hero=hero, guide=guide, prize=prize, gear=gear, place=place, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a small child about {f["hero"].id}, curiosity, and a twist in {f["place"].label}.',
        f"Tell a gentle tale where {f['hero'].id} must crouch through a tum-dim place with help from {f['guide'].id}.",
        f'Write a simple adventure ending with a found {f["prize"].phrase} and a safe, happy return.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prize, place = f["hero"], f["guide"], f["prize"], f["place"]
    return [
        QAItem(
            question=f"Who went into {place.label} looking for {prize.phrase}?",
            answer=f"{hero.id} went with {guide.id} into {place.label} looking for {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {hero.id} have to crouch in the story?",
            answer=f"{place.label} was tum-dim, so {hero.id} had to crouch to move safely through it.",
        ),
        QAItem(
            question=f"What changed the search into a bigger adventure?",
            answer=f"A twist in the path opened a hidden side-way, so the search became a new adventure.",
        ),
        QAItem(
            question=f"What did {hero.id} find at the end?",
            answer=f"{hero.id} found {prize.phrase} and held it up at the end of the adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a twist in a path?",
            answer="A twist is a turn or bend that changes where the path goes.",
        ),
        QAItem(
            question="Why do people crouch in small spaces?",
            answer="People crouch to make their bodies smaller so they can fit through low or narrow places.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_program("#show eligible/2.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "eligible"))
    py = {(p, prize) for p in PLACES for prize in PRIZES if reasonableness_gate(PLACES[p], prize)}
    if atoms == py:
        print(f"OK: ASP parity matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("ASP only:", sorted(atoms - py))
    print("PY only:", sorted(py - atoms))
    return 1


def asp_candidates() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show eligible/2."))
    return sorted(set(asp.atoms(model, "eligible")))


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="tunnel", hero_name="Mira", hero_type="girl", guide_name="Mom", guide_type="mother", path="crawl", prize="key"),
    StoryParams(place="cave", hero_name="Finn", hero_type="boy", guide_name="Dad", guide_type="father", path="crawl", prize="lantern"),
    StoryParams(place="ruins", hero_name="Lina", hero_type="girl", guide_name="Grandma", guide_type="guide", path="explore", prize="shell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show eligible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_candidates()
        print(f"{len(pairs)} eligible place/prize pairs:")
        for place, prize in pairs:
            print(f"  {place} {prize}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
