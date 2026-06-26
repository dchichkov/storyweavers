#!/usr/bin/env python3
"""
storyworlds/worlds/thistle_blimp_pamphlet_bravery_happy_ending_misunderstanding.py
===================================================================================

A small pirate-tale storyworld about a brave little crew, a blimp full of
pamphlets, a prickly thistle patch, and a misunderstanding that turns into a
happy ending.

The source tale inspiration:
---
A tiny pirate feels worried when a blimp drops a pamphlet about bravery near a
thistle patch. The captain thinks the pamphlet is a dare, but it is really an
invitation to a town pageant. After a misunderstanding, the pirate proves brave
by fetching the pamphlet from the thistles, and the crew cheers. The blimp
returns, the mistake is cleared up, and everyone ends the day smiling.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"captain", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    has_thistles: bool = False
    has_port: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    captain_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misunderstanding(world: World) -> list[str]:
    hero = world.get("hero")
    captain = world.get("captain")
    pamphlet = world.get("pamphlet")
    if hero.memes.get("worry", 0.0) < THRESHOLD:
        return []
    sig = ("misunderstanding",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["misunderstanding"] = captain.memes.get("misunderstanding", 0.0) + 1
    return [f"The captain took the pamphlet the wrong way and frowned."]


def _r_bravery(world: World) -> list[str]:
    hero = world.get("hero")
    pamphlet = world.get("pamphlet")
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return []
    if pamphlet.meters.get("retrieved", 0.0) >= THRESHOLD:
        return []
    sig = ("brave_retrieve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pamphlet.meters["retrieved"] = 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    return [f"{hero.id} reached into the thistles and snatched the pamphlet free."]


def _r_happy_ending(world: World) -> list[str]:
    hero = world.get("hero")
    captain = world.get("captain")
    pamphlet = world.get("pamphlet")
    if pamphlet.meters.get("retrieved", 0.0) < THRESHOLD:
        return []
    if captain.memes.get("understanding", 0.0) >= THRESHOLD:
        return []
    sig = ("happy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["understanding"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    captain.memes["joy"] = captain.memes.get("joy", 0.0) + 1
    return [f"The captain laughed, saw the truth, and called it a happy ending."]


CAUSAL_RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("bravery", _r_bravery),
    Rule("happy_ending", _r_happy_ending),
]


@dataclass
class RegistryItem:
    id: str
    label: str
    phrase: str = ""


PLACES = {
    "harbor": Place(name="the harbor", has_port=True),
    "garden_island": Place(name="the island garden", has_thistles=True),
    "dock": Place(name="the dock", has_port=True),
}


HEROES = {
    "pip": {"name": "Pip", "type": "pirate"},
    "mara": {"name": "Mara", "type": "pirate"},
    "jory": {"name": "Jory", "type": "pirate"},
}


PAMPHLETS = {
    "bravery_pamphlet": RegistryItem(
        id="bravery_pamphlet",
        label="pamphlet",
        phrase="a bright pamphlet about bravery",
    ),
}


def tell(place: Place, hero_name: str, captain_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type="pirate", label=hero_name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=captain_name))
    pamphlet = world.add(Entity(
        id="pamphlet",
        kind="thing",
        type="pamphlet",
        label="pamphlet",
        phrase="a bright pamphlet about bravery",
        caretaker="captain",
    ))

    hero.meters["near_thistles"] = 1.0 if place.has_thistles else 0.0
    hero.memes["worry"] = 1.0
    hero.memes["bravery"] = 0.0
    captain.memes["hope"] = 1.0

    world.say(
        f"On {place.name}, {hero_name} spotted {pamphlet.phrase} fluttering from a blimp."
    )
    world.say(
        f"The little pirate thought the blimp had dropped a challenge, and {captain_name} "
        f"thought the note was meant to shame the crew."
    )
    world.para()
    world.say(
        f"But the wind carried the paper into a prickly thistle patch, and the whole crew "
        f"stared at it as if it were a mystery."
    )

    hero.memes["worry"] += 1
    hero.memes["bravery"] += 1
    propagate(world, narrate=True)

    world.para()
    if pamphlet.meters.get("retrieved", 0.0) >= THRESHOLD:
        world.say(
            f"{hero_name} held the pamphlet high, and the blimp's pilot waved down with a grin."
        )
        world.say(
            f"The captain finally read it properly: it was an invitation to a seaside pageant, "
            f"not a scolding at all."
        )
    world.say(
        f"That evening, the crew shared sea-sweet cake by the dock, and the blimp drifted "
        f"away while everyone laughed about the misunderstanding."
    )

    world.facts.update(
        hero=hero,
        captain=captain,
        pamphlet=apamphlet if False else pamphlet,
        place=place,
        hero_name=hero_name,
        captain_name=captain_name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale about a blimp, a thistle patch, and a brave child.',
        f"Tell a story where {f['hero_name']} mistakes a pamphlet from a blimp for a challenge and then learns it was a friendly invitation.",
        "Write a gentle pirate story with a misunderstanding that ends in a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"Where did {f['hero_name']} find the pamphlet?",
            answer=f"{f['hero_name']} found it near {place.name}, where the thistles made the paper hard to reach.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding in the story?",
            answer=(
                f"{f['captain_name']} thought the pamphlet was a rude challenge, but it was really a friendly invitation "
                f"from the blimp's pilot."
            ),
        ),
        QAItem(
            question=f"What brave thing did {f['hero_name']} do?",
            answer=(
                f"{f['hero_name']} reached into the thistles and pulled the pamphlet free, which showed bravery even though the leaves were prickly."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                "The captain understood the mistake, everyone laughed, and the day ended like a happy ending by the dock."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thistle?",
            answer="A thistle is a prickly plant with sharp leaves, so touching it can sting a little.",
        ),
        QAItem(
            question="What is a blimp?",
            answer="A blimp is a big balloon-like flying machine that can drift slowly over land or water.",
        ),
        QAItem(
            question="What is a pamphlet?",
            answer="A pamphlet is a small paper booklet or flyer that shares a message or invitation.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or difficult even when you feel nervous.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.type:10} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_params() -> list[tuple[str, str, str]]:
    return [(p, h, c) for p in PLACES for h in HEROES for c in ["Redbeard", "Captain Sails"]]


def explain_rejection(place: str) -> str:
    return f"(No story: {place} does not fit this little pirate tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with thistle, blimp, pamphlet, bravery, misunderstanding, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--captain")
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
    if place not in PLACES:
        raise StoryError(explain_rejection(place))
    hero_name = args.name or rng.choice([v["name"] for v in HEROES.values()])
    captain_name = args.captain or rng.choice(["Redbeard", "Captain Sails", "Old Finch"])
    return StoryParams(place=place, hero_name=hero_name, captain_name=captain_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero_name, params.captain_name)
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


ASP_RULES = r"""
#show valid/3.
place(harbor).
place(garden_island).
place(dock).
hero(pip).
hero(mara).
hero(jory).
captain(redbeard).
captain(captain_sails).
valid(P,H,C) :- place(P), hero(H), captain(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for c in ["redbeard", "captain_sails"]:
        lines.append(asp.fact("captain", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(""))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_params())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_params() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_params():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            p = StoryParams(place=place, hero_name="Pip", captain_name="Redbeard")
            samples.append(generate(p))
    else:
        for i in range(max(args.n, 1)):
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
