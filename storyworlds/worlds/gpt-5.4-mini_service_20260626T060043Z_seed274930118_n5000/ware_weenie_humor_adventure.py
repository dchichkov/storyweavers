#!/usr/bin/env python3
"""
storyworlds/worlds/ware_weenie_humor_adventure.py
==================================================

A tiny adventure-comedy storyworld about a traveling helper, a curious weenie,
and a troublesome piece of wares that must be carried carefully.

Seed tale:
---
A small caravan arrived at the hill market with a crate of shiny ware. Pip, a
tiny weenie dog with a heroic nose, wanted to help deliver the crate to the
stall at the top of the steps. But the crate was wobbly, the steps were steep,
and every time Pip barked too hard, the lid jigged open and the odd wares slid
around. The keeper warned Pip, then laughed, then found a clever way to make
the trip easier: a padded harness and a rolling dolly. Pip pulled proudly, the
crate stayed safe, and the market day ended in cheerful, silly triumph.

World model:
---
- Physical meters:
    * load, wobble, scramble, sparkle, dust, pride
- Emotional memes:
    * curiosity, worry, courage, humor, teamwork, relief

Adventure-comedy premise:
---
A small courier wants to move a crate of "ware" up a hill. A tiny "weenie"
dog wants to help. The dangerous turn is the wobble of the crate and the silly
noise of the dog, which threatens to scatter the goods. The resolution is a
practical, compatible fix: a padded harness and a rolling dolly, turning the
hard climb into a proud little expedition.
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
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    description: str
    uphill: bool = True


@dataclass
class Cargo:
    label: str
    phrase: str
    mess: str
    trouble: str
    region: str
    keyword: str


@dataclass
class HelperGear:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    tail: str


@dataclass
class StoryParams:
    place: str
    cargo: str
    name: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _join(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


SETTINGS = {
    "hill_market": Setting(
        place="the hill market",
        description="a bright market perched above the town square",
        uphill=True,
    ),
    "harbor_steps": Setting(
        place="the harbor steps",
        description="a windy stone stairway between the pier and the shops",
        uphill=True,
    ),
    "orchard_lane": Setting(
        place="the orchard lane",
        description="a long lane with carts, apples, and a lot of bumping cobbles",
        uphill=False,
    ),
}

CARGO = {
    "ware": Cargo(
        label="ware",
        phrase="a crate of shiny ware",
        mess="scatter",
        trouble="the lid jiggles and the shiny pieces tumble about",
        region="crate",
        keyword="ware",
    ),
    "tins": Cargo(
        label="tins",
        phrase="a stack of tin ware",
        mess="clatter",
        trouble="the tins rattle so loudly they sound like tiny bells",
        region="crate",
        keyword="ware",
    ),
    "glass": Cargo(
        label="glass",
        phrase="a box of delicate ware",
        mess="shatter",
        trouble="the glassy bits wobble and threaten to knock together",
        region="crate",
        keyword="ware",
    ),
}

HELPERS = [
    HelperGear(
        id="harness",
        label="a padded harness",
        phrase="a padded harness",
        helps={"pull", "steady"},
        covers={"chest", "shoulders"},
        tail="Pip tugged from a steadier angle",
    ),
    HelperGear(
        id="dolly",
        label="a rolling dolly",
        phrase="a rolling dolly",
        helps={"carry", "roll"},
        covers={"ground"},
        tail="the dolly took the heaviest bumps",
    ),
    HelperGear(
        id="blanket",
        label="a soft blanket wrap",
        phrase="a soft blanket wrap",
        helps={"protect", "cushion"},
        covers={"crate"},
        tail="the blanket cushioned the crate with a snug little hug",
    ),
]

NAMES = ["Pip", "Milo", "Tess", "Nia", "Bo", "Jory", "Luna", "Zed"]
PARENTS = ["keeper", "uncle", "aunt", "captain"]
TRAITS = ["cheerful", "curious", "spirited", "brave", "silly"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for cargo in CARGO:
            combos.append((place, cargo))
    return combos


def choose_gear(cargo: Cargo) -> HelperGear:
    if cargo.label == "ware":
        return HELPERS[0]
    if cargo.label == "tins":
        return HELPERS[1]
    return HELPERS[2]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.cargo not in CARGO:
        raise StoryError("Unknown cargo.")
    if params.parent not in PARENTS:
        raise StoryError("Unknown caretaker role.")


def predict_mishap(world: World, hero: Entity, cargo: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["worry"] += 0.5
    sim.get(hero.id).meters["wobble"] += 1.0
    sim.get(cargo.id).meters["scramble"] += 1.0
    soiled = sim.get(cargo.id).meters["scramble"] >= THRESHOLD
    return {"soiled": soiled, "humor": True}


def setup(world: World, hero: Entity, caretaker: Entity, cargo: Entity) -> None:
    world.say(
        f"{hero.id} was {hero.label} and loved helping with big little jobs."
    )
    world.say(
        f"At {world.setting.place}, {caretaker.label} guarded {cargo.phrase} "
        f"while the day buzzed with wagons and polite shouting."
    )
    world.say(
        f"{hero.id} especially loved the word {cargo.label}; it sounded funny, "
        f"like something that should wear a hat."
    )


def start_trip(world: World, hero: Entity, caretaker: Entity, cargo: Entity) -> None:
    world.para()
    world.say(
        f"One market morning, {hero.id} wanted to help carry the crate up the hill."
    )
    world.say(
        f"{hero.id} trotted beside {caretaker.label}, tail high, as if the whole path "
        f"had been built for {hero.pronoun('object')} alone."
    )


def warn(world: World, caretaker: Entity, hero: Entity, cargo: Entity) -> bool:
    pred = predict_mishap(world, hero, cargo)
    if not pred["soiled"]:
        return False
    world.say(
        f'"Careful," {caretaker.label} said. "If the crate bounces too much, '
        f"that {cargo.label} will {cargo.mess} everywhere."'
    )
    return True


def comedy_tension(world: World, hero: Entity, caretaker: Entity, cargo: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    world.say(
        f"{hero.id} gave a tiny bark that sounded like a squeaky trumpet."
    )
    world.say(
        f"The crate answered with a wobble; {cargo.trouble}, and everyone made the "
        f"same worried face for one silly second."
    )


def offer_fix(world: World, caretaker: Entity, hero: Entity, cargo: Entity) -> HelperGear:
    gear = choose_gear(cargo)
    world.say(
        f'{caretaker.label} sniffed once, then smiled. "How about {gear.phrase} '
        f'and a little more balance?"'
    )
    return gear


def apply_fix(world: World, hero: Entity, caretaker: Entity, cargo: Entity, gear: HelperGear) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    hero.meters["pride"] = hero.meters.get("pride", 0.0) + 1
    cargo.meters["scramble"] = max(0.0, cargo.meters.get("scramble", 0.0) - 1)
    world.say(
        f"{hero.id} strapped on {gear.label} and stood taller."
    )
    world.say(
        f"With {gear.tail}, {hero.id} could help without bumping the crate so hard."
    )
    world.say(
        f"Soon the climb turned into a tiny parade: {hero.id} helping, {caretaker.label} "
        f"laughing, and {cargo.label} staying neatly inside the crate."
    )
    world.say(
        f"At the top, the market stall waited like a reward, and the day felt as "
        f"grand as a treasure hunt."
    )


def tell(setting: Setting, cargo_cfg: Cargo, hero_name: str = "Pip", parent_role: str = "keeper") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="dog",
        label="a tiny weenie dog",
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=parent_role,
        label=f"the {parent_role}",
    ))
    cargo = world.add(Entity(
        id="Cargo",
        kind="thing",
        type=cargo_cfg.label,
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        caretaker=caretaker.id,
        plural=True if cargo_cfg.label == "tins" else False,
    ))
    cargo.meters["scramble"] = 0.0
    hero.memes["humor"] = 0.0

    setup(world, hero, caretaker, cargo)
    start_trip(world, hero, caretaker, cargo)
    warned = warn(world, caretaker, hero, cargo)
    comedy_tension(world, hero, caretaker, cargo)

    world.para()
    if warned:
        gear = offer_fix(world, caretaker, hero, cargo)
        apply_fix(world, hero, caretaker, cargo, gear)
    else:
        world.say(
            f"No one had to stop the march, because the crate stayed calm enough "
            f"for the short climb."
        )
        world.say(
            f"{hero.id} still looked delighted, because helping on a hill felt like "
            f"an adventure even on an easy day."
        )

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        cargo=cargo,
        setting=setting,
        gear=choose_gear(cargo),
        warned=warned,
    )
    return world


KNOWLEDGE = {
    "ware": [
        (
            "What is ware?",
            "Ware is a word for goods or useful things that are made to be sold or carried from place to place.",
        )
    ],
    "weenie": [
        (
            "What is a weenie dog?",
            "A weenie dog is a small dog with a long body and short legs, and it can look very funny when it trots.",
        )
    ],
    "harness": [
        (
            "What is a harness for?",
            "A harness helps hold or guide a person or animal so they can pull safely without straining too hard.",
        )
    ],
    "dolly": [
        (
            "What is a dolly for?",
            "A dolly is a small cart with wheels that helps carry heavy things without lifting them all the time.",
        )
    ],
    "blanket": [
        (
            "Why use a blanket to wrap something?",
            "A blanket can keep something safe and cushioned so it does not bump or scratch so easily.",
        )
    ],
    "market": [
        (
            "What happens at a market?",
            "At a market, people bring things to buy and sell, and the place can be busy, colorful, and noisy.",
        )
    ],
}
KNOWLEDGE_ORDER = ["market", "ware", "weenie", "harness", "dolly", "blanket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, caretaker, cargo = f["hero"], f["caretaker"], f["cargo"]
    return [
        f'Write a short adventure story for a young child that uses the words "{cargo.label}" and "weenie".',
        f"Tell a funny hill-climb story where {hero.id}, a tiny weenie dog, helps {caretaker.label} carry {cargo.phrase}.",
        f"Write a gentle, humorous adventure about careful teamwork at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caretaker, cargo, setting = f["hero"], f["caretaker"], f["cargo"], f["setting"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"Who wanted to help carry the crate at {setting.place}?",
            answer=f"{hero.id}, a tiny weenie dog, wanted to help {caretaker.label} carry the crate.",
        ),
        QAItem(
            question=f"What was inside the crate that made the trip tricky?",
            answer=f"The crate held {cargo.phrase}, and the {cargo.label} could get scattered if the box bounced too much.",
        ),
        QAItem(
            question=f"What did {caretaker.label} give {hero.id} to make the climb safer?",
            answer=f"{caretaker.label} gave {hero.id} {gear.phrase} and a steadier way to help with the load.",
        ),
    ]
    if f.get("warned"):
        qa.append(
            QAItem(
                question=f"Why did {caretaker.label} worry about the crate?",
                answer=f"{caretaker.label} worried because the crate kept wobbling, and the {cargo.label} might {cargo.mess} all over the path.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end for {hero.id} and the crate?",
            answer=f"They reached the top together, the crate stayed safe, and {hero.id} felt proud after helping on the hill.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"market", "weenie", "harness", "dolly", "blanket", world.facts["cargo"].label}
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A cargo is at risk when the route is uphill and the crate can wobble.
at_risk(C) :- cargo(C), wobble_risk(C).

% A gear is a compatible fix when it can reduce the wobble and help with the load.
compatible(G, C) :- gear(G), cargo(C), fix(G, C).

valid_story(Place, Cargo, Gear) :- setting(Place), cargo(Cargo), gear(Gear),
                                   route(Place), at_risk(Cargo), compatible(Gear, Cargo).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.uphill:
            lines.append(asp.fact("route", sid))
    for cid, c in CARGO.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("wobble_risk", cid))
        lines.append(asp.fact("mess_kind", cid, c.mess))
    for g in HELPERS:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.helps):
            lines.append(asp.fact("fix", g.id, ckey_for_help(h)))
    return "\n".join(lines)


def ckey_for_help(help_word: str) -> str:
    return {
        "pull": "ware",
        "steady": "ware",
        "carry": "tins",
        "roll": "tins",
        "protect": "glass",
        "cushion": "glass",
    }.get(help_word, "ware")


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    # Python gate is intentionally simple here; compare the story-valid triples.
    py = sorted((place, cargo, choose_gear(CARGO[cargo]).id) for place, cargo in valid_combos())
    cl = asp_valid_stories()
    cl2 = sorted((a, b, c) for (a, b, c) in cl)
    if py == cl2:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  python:", py)
    print("  clingo :", cl2)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous adventure storyworld about ware and a weenie dog.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.cargo:
        combos = [c for c in combos if c[1] == args.cargo]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, cargo = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, cargo=cargo, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(SETTINGS[params.place], CARGO[params.cargo], hero_name=params.name, parent_role=params.parent)
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
    StoryParams(place="hill_market", cargo="ware", name="Pip", parent="keeper"),
    StoryParams(place="harbor_steps", cargo="tins", name="Milo", parent="captain"),
    StoryParams(place="orchard_lane", cargo="glass", name="Tess", parent="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:\n")
        for t in triples:
            print(" ", t)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.cargo} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
