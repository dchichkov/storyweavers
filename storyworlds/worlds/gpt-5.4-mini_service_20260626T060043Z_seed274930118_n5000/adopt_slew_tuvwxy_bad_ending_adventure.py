#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/adopt_slew_tuvwxy_bad_ending_adventure.py
===============================================================================================================

A small, classical adventure storyworld with a deliberately bad ending.

Seed-tale sketch:
---
A young explorer follows an old map into a dark ravine. Along the way, the
explorer finds a tiny lost creature named Tuvwxy and decides to adopt it.
Deeper in the ravine, a cave brute blocks the only bridge home. The explorer
tries to slew the brute, but the attempt goes wrong. The bridge breaks, the
map is lost, and the explorer ends the day stranded with Tuvwxy.

This world keeps the scope small: one quest, one companion, one threat, one
hard turn, and one unhappy ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    shadow: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    danger: str
    injury: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "ravine": Place(label="the ravine", shadow="the dark ravine", afford={"adopt", "slew"}),
    "cave": Place(label="the cave", shadow="the cave mouth", afford={"adopt", "slew"}),
    "ruins": Place(label="the old ruins", shadow="the broken arch", afford={"adopt", "slew"}),
}

QUESTS = {
    "slew": Quest(
        id="slew",
        verb="slew the cave brute",
        gerund="facing the cave brute",
        danger="the brute had sharp claws and a hard club",
        injury="scratched and pinned",
        tags={"battle", "brute"},
    ),
    "adopt": Quest(
        id="adopt",
        verb="adopt the lost creature",
        gerund="caring for the lost creature",
        danger="the little creature was scared and could not keep up",
        injury="late and lost",
        tags={"companion", "lost"},
    ),
}

SOURCES = {
    "tuvwxy": Entity(id="Tuvwxy", kind="character", type="thing", label="Tuvwxy"),
}

TRAITS = ["brave", "curious", "quick", "restless", "bold"]
NAMES = ["Milo", "June", "Iris", "Nico", "Pia", "Arlo"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure world with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, quest) for place, p in SETTINGS.items() for quest in p.afford if quest in QUESTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.place and args.quest not in SETTINGS[args.place].afford:
        raise StoryError("That quest does not fit that place.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("No valid adventure matches the given options.")
    place, quest = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, trait=trait)


def _do_adopt(world: World, hero: Entity, pet: Entity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    pet.owner = hero.id
    pet.carried_by = hero.id
    pet.memes["trust"] = pet.memes.get("trust", 0.0) + 1


def _do_slew(world: World, hero: Entity, brute: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.meters["strain"] = hero.meters.get("strain", 0.0) + 1
    brute.meters["anger"] = brute.meters.get("anger", 0.0) + 1
    if hero.meters["strain"] >= THRESHOLD:
        world.fired.add(("bad_turn",))


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    brute = world.add(Entity(id="Brute", kind="character", type="thing", label="the cave brute"))
    pet = world.add(Entity(id="Tuvwxy", kind="character", type="thing", label="Tuvwxy"))
    map_item = world.add(Entity(id="Map", type="thing", label="the old map", owner=hero.id))
    torch = world.add(Entity(id="Torch", type="thing", label="a small torch", owner=hero.id))

    world.say(
        f"{hero.id} was a {params.trait} little {params.gender} who loved adventure and kept an old map in "
        f"{hero.pronoun('possessive')} pack."
    )
    world.say(
        f"One gray morning, {hero.id} went into {world.place.shadow} with a torch, hoping to {QUESTS[params.quest].verb}."
    )

    world.para()
    world.say(
        f"Near a fallen stone, {hero.id} found Tuvwxy, a tiny lost creature shivering in the dust."
    )
    _do_adopt(world, hero, pet)
    world.say(
        f"{hero.id} could not leave Tuvwxy behind, so {hero.pronoun()} chose to adopt {pet.id} and carry "
        f"{pet.it()} deeper into the ravine."
    )

    world.para()
    if params.quest == "slew":
        world.say(
            f"At the bridge, the cave brute stepped out of the shadows and blocked the only path home."
        )
        world.say(
            f"{QUESTS[params.quest].danger.capitalize()}. {hero.id} lifted the torch, rushed forward, and tried to {QUESTS[params.quest].verb}."
        )
        _do_slew(world, hero, brute)
        world.say(
            f"But the stone underfoot cracked, the bridge gave way, and the old map slipped into the chasm."
        )
        map_item.carried_by = None
        map_item.owner = None
        hero.meters["lost"] = hero.meters.get("lost", 0.0) + 1
        hero.memes["hopeless"] = hero.memes.get("hopeless", 0.0) + 1
        world.say(
            f"{hero.id} ended the day stranded on the far side of the gap with Tuvwxy trembling in "
            f"{hero.pronoun('possessive')} arms and no clear way back."
        )
    else:
        world.say(
            f"Farther in, the cave brute thundered out of the dark and snarled at the little pair."
        )
        world.say(
            f"{hero.id} wanted to protect Tuvwxy and reach home, but the path was too steep, and the torch guttered low."
        )
        hero.meters["lost"] = hero.meters.get("lost", 0.0) + 1
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
        map_item.carried_by = None
        map_item.owner = None
        world.say(
            f"When the brute stamped the ground, {hero.id} dropped the map, and the wind carried it into the dark."
        )
        world.say(
            f"{hero.id} hugged Tuvwxy close, yet both of them were still trapped in the ravine as night shut the sky."
        )

    world.facts = {
        "hero": hero,
        "pet": pet,
        "brute": brute,
        "map": map_item,
        "torch": torch,
        "params": params,
        "quest": QUESTS[params.quest],
        "place": SETTINGS[params.place],
        "bad_end": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    q = world.facts["quest"]
    return [
        f"Write a short Adventure-style story about {p.name} trying to {q.verb} in {world.place.label}.",
        f"Tell a child-friendly adventure where {p.name} finds Tuvwxy and makes a hard choice in {world.place.label}.",
        f"Write a brief quest story with a bad ending: a lost map, a cave threat, and Tuvwxy in the hero's arms.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    pet: Entity = f["pet"]
    brute: Entity = f["brute"]
    q: Quest = f["quest"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the adventure about?",
            answer=f"It was about {hero.id}, a {hero.memes.get('care', 0.0) and 'kind' or 'brave'} little {hero.type} who went into {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} try to do in {place.label}?",
            answer=f"{hero.id} tried to {q.verb}.",
        ),
        QAItem(
            question=f"Who did {hero.id} adopt?",
            answer=f"{hero.id} adopted Tuvwxy and carried {pet.it()} through the ravine.",
        ),
        QAItem(
            question=f"What went wrong at the end of the story?",
            answer=(
                f"The bridge broke and the old map was lost, so {hero.id} ended up stranded with Tuvwxy instead of going home."
            ),
        ),
        QAItem(
            question=f"Why was the cave brute a problem?",
            answer=f"The cave brute blocked the way home and made the path dangerous.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an old map for?",
            answer="An old map helps a traveler find a path through a place that is hard to explore.",
        ),
        QAItem(
            question="Why can a bridge be important in an adventure?",
            answer="A bridge can be important because it helps a traveler cross water or a gap and get home.",
        ),
        QAItem(
            question="What does it mean to adopt a lost creature?",
            answer="To adopt a lost creature means to take care of it and keep it safe.",
        ),
        QAItem(
            question="What does slewing a monster mean in a story?",
            answer="Slewing a monster means trying to defeat it in battle.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ravine", quest="slew", name="Milo", gender="boy", trait="brave"),
    StoryParams(place="cave", quest="adopt", name="June", gender="girl", trait="curious"),
]


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- action(Q).
valid(P,Q) :- setting(P), action(Q), afford(P,Q).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(place.afford):
            lines.append(asp.fact("afford", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("action", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(f"{len(combos)} compatible adventure combos:\n")
        for place, quest in combos:
            print(f"  {place:8} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            header = f"### {p.name}: {p.quest} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
