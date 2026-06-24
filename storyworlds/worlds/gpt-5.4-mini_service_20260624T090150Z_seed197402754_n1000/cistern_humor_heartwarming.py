#!/usr/bin/env python3
"""
cistern_humor_heartwarming.py
==============================

A small storyworld about a child, a cistern, a small mishap, and a kind fix.

The seed image:
---
A child wants to peek into an old cistern in a sunny yard. The cistern echoes
silly sounds, which makes the child laugh. Then a bucket slips, splashes water
everywhere, and the grown-up worries the water might get dirty. Together they
use a cloth, a lid, and a careful plan so the cistern stays safe.

This world keeps the story close to heartwarming, with a little humor from echo
games and a gentle ending that shows what changed.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    echo: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risky: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    ending: str
    guards: set[str]
    covers: set[str]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.facts = dict(self.facts)
        return w


MESS = {"wet", "muddy"}
THRESHOLD = 1.0

PLACES = {
    "yard": Place(name="the sunny yard", echo=True, afford={"peek", "fetch"}),
    "courtyard": Place(name="the courtyard", echo=True, afford={"peek", "fetch"}),
    "garden": Place(name="the garden", echo=False, afford={"peek", "fetch"}),
}

ACTIONS = {
    "peek": Action(
        id="peek",
        verb="peek into the cistern",
        gerund="peeking into the cistern",
        risky="lean too far over the stone rim",
        mess="wet",
        soil="splashed and damp",
        tags={"cistern", "water", "echo"},
    ),
    "fetch": Action(
        id="fetch",
        verb="fetch water from the cistern",
        gerund="drawing water from the cistern",
        risky="swing the bucket too fast",
        mess="wet",
        soil="wet and slippery",
        tags={"cistern", "water"},
    ),
}

PRIZES = {
    "shirt": Prize(id="shirt", label="shirt", phrase="a clean blue shirt", region="torso"),
    "apron": Prize(id="apron", label="apron", phrase="a little apron with pockets", region="torso"),
    "boots": Prize(id="boots", label="boots", phrase="new boots", region="feet", plural=True),
}

GEAR = {
    "lid": Gear(
        id="lid",
        label="a wooden lid",
        prep="set the wooden lid back on the cistern",
        ending="they set the wooden lid down tight over the cistern",
        guards={"wet"},
        covers={"torso", "feet"},
    ),
    "cloth": Gear(
        id="cloth",
        label="a thick cloth",
        prep="wrap the thick cloth around the bucket handle",
        ending="they used the thick cloth to hold the bucket steady",
        guards={"wet"},
        covers={"torso", "feet"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ivy", "Ben", "Ava", "Theo"]
TRAITS = ["curious", "cheerful", "gentle", "brave", "playful"]


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region == "torso" or action.id == "fetch"


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if action.mess in gear.guards:
            return gear
    return None


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.echo:
            lines.append(asp.fact("echo", pid))
        for a in sorted(place.afford):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, prid))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gid, g))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gid, c))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,P) :- mess_of(A,M), prize(P), worn_on(P,R), splashes(A,R).
splashes(peek,torso). splashes(peek,feet).
splashes(fetch,torso). splashes(fetch,feet).
fix(A,P) :- risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), risk(A,P), fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for act_id, act in ACTIONS.items():
            if act_id not in place.afford:
                continue
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place_id, act_id, prize_id))
    return out


def _intro(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in child.memes if False) if False else child.type} "
        f"who liked to listen to silly echoes."
    )


def build_story(world: World, child: Entity, adult: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"{child.id} was a {world.facts['trait']} {child.type} who loved {action.gerund}."
    )
    world.say(
        f"{child.id}'s {adult.type} had bought {child.pronoun('object')} {prize.phrase}."
    )
    world.say(
        f"{child.id} liked {prize.it()} very much and wore {prize.it()} every day."
    )

    world.para()
    if world.place.echo:
        world.say(
            f"One bright day, {child.id} and {child.pronoun('possessive')} {adult.type} went to {world.place.name}."
        )
        world.say(
            f"{child.id} leaned over the old cistern and called, 'Hello, hello!'"
        )
        world.say(
            f"The cistern answered with a funny echo, as if a tiny duck were saying hello back."
        )
        world.say(
            f"{child.id} giggled so hard that {child.pronoun('possessive')} shoulders wiggled."
        )

    world.say(
        f"Then {child.id} tried to {action.risky}."
    )
    world.say(
        f"The bucket tipped, and water splashed {action.soil} onto {child.pronoun('possessive')} {prize.label}."
    )
    prize.meters[action.mess] = 1.0
    child.memes["oops"] = 1.0
    adult.memes["worry"] = 1.0

    world.para()
    world.say(
        f"{child.pronoun('possessive').capitalize()} {adult.type} did not scold {child.id}."
    )
    world.say(
        f'"That cistern is funny, but it is also old," {adult.id} said kindly.'
    )
    world.say(
        f'"Let us keep it safe and dry together."'
    )

    gear = select_gear(action, prize)
    if gear:
        world.say(
            f"{child.id} nodded, and {child.pronoun('possessive')} {adult.type} found {gear.label}."
        )
        world.say(
            f"They {gear.prep}, then {gear.ending}."
        )
        child.memes["joy"] = 2.0
        child.memes["calm"] = 1.0
        adult.memes["pride"] = 1.0
        prize.meters["wet"] = 0.0
        world.say(
            f"{child.id} laughed again, this time because the cistern's echo made {child.id}'s own laugh sound extra round and silly."
        )
        world.say(
            f"In the end, {child.id} was still smiling, {prize.label} was safe, and the cistern had its lid on like a tidy hat."
        )


def make_world(params) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    adult = world.add(Entity(id="grownup", kind="character", type=params.parent))
    prize = world.add(Entity(id="prize", type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=child.id))
    world.facts.update(
        child=child, adult=adult, prize=prize,
        trait=params.trait, action=ACTIONS[params.action], place=PLACES[params.place],
    )
    build_story(world, child, adult, prize, ACTIONS[params.action])
    return world


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short heartwarming story for a child about a cistern, an echo, and a kind fix.',
        f"Tell a gentle story where {f['child'].id} wants to {f['action'].verb} and gets a little splashy, then everyone solves it kindly.",
        f'Write a simple story that includes the word "cistern" and ends with a safe, happy cleanup.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    prize = f["prize"]
    action = f["action"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a {f['trait']} {child.type}, and {child.pronoun('possessive')} kind {adult.type}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do at {place.name}?",
            answer=f"{child.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"Why did the grown-up worry about the {prize.label}?",
            answer=f"The grown-up worried because water splashed onto {child.pronoun('possessive')} {prize.label} and could make it wet.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with everyone choosing a safe fix, so {child.id} could laugh, the cistern stayed safe, and the {prize.label} was okay.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cistern?",
            answer="A cistern is a container or tank that holds water, often in a yard or under a building.",
        ),
        QAItem(
            question="Why can echoes sound funny?",
            answer="An echo is a sound that bounces back, so it can make your voice sound repeated or silly.",
        ),
        QAItem(
            question="Why should old water places be treated carefully?",
            answer="Old water places can be deep or slippery, so it is safer to use them carefully and with help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="yard", action="peek", prize="shirt", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="courtyard", action="fetch", prize="boots", name="Leo", gender="boy", parent="father", trait="playful"),
    StoryParams(place="garden", action="peek", prize="apron", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: cistern, humor, heartwarming.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    action = args.action or rng.choice(sorted(PLACES[place].afford))
    prize = args.prize or rng.choice(list(PRIZES))
    if args.gender and prize in PRIZES and args.gender not in PRIZES[prize].genders:
        raise StoryError("That prize does not fit that gender in this tiny world.")
    if action not in PLACES[place].afford:
        raise StoryError("That action does not fit the place.")
    if not prize_at_risk(ACTIONS[action], PRIZES[prize]) or not select_gear(ACTIONS[action], PRIZES[prize]):
        raise StoryError("No honest story can be told with that action and prize.")
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.")
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n")
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
