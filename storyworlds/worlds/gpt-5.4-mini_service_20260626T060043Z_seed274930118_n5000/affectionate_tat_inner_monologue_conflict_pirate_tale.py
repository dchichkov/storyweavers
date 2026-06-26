#!/usr/bin/env python3
"""
A small pirate-tale story world with affectionate inner-monologue conflict.

Premise:
- A young pirate finds a tat of an old keepsake.
- The pirate wants to keep sailing, but the tat matters to a companion.
- The captain's inner monologue weighs pride against affection.
- A conflict turns into a gentle repair and a shared vow.

This world generates a single complete child-friendly pirate story with a
state-driven middle turn and a concrete ending image.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "mate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the harbor"
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    region: str
    value: str


@dataclass
class Gear:
    id: str
    label: str
    fixes: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.choice: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.choice = self.choice
        return clone


SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"repair", "sort"}),
    "ship": Setting(place="the little ship", affords={"repair", "sail"}),
    "island": Setting(place="the tiny island", affords={"repair", "search"}),
}

TREASURES = {
    "tat": Treasure(label="tat", phrase="an old tat with a faded heart stitched on it", region="chest", value="precious"),
    "map": Treasure(label="map", phrase="a tatty map wrapped in cloth", region="hand", value="important"),
    "flag": Treasure(label="flag", phrase="a little flag with a soft red tat", region="mast", value="special"),
}

GEAR = [
    Gear(id="needle", label="a gold needle and thread", fixes={"tat"}, prep="stitch the tat neat again", tail="mended the little tat until it looked brave"),
    Gear(id="cloth", label="a clean scrap of cloth", fixes={"map", "flag"}, prep="wrap it in clean cloth", tail="tied the cloth gently around the keepsake"),
]

PIRATE_NAMES = ["Mina", "Jory", "Pip", "Nell", "Rafe", "Tessa"]
MATES = ["first mate", "shipmate", "captain"]
TRAITS = ["affectionate", "brave", "cheery", "stubborn", "careful"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A treasure is at risk if the setting and chosen action disturb its region.
at_risk(T) :- treasure(T), fragile(T), chosen(A), disturbs(A, R), stored_on(T, R).

% A fix exists only if a tool actually handles the trouble.
fix(T) :- at_risk(T), chosen(A), tool(G), solves(G, Trouble), trouble_of(A, Trouble), matches(G, T).

valid_story(P, T) :- setting(P), treasure(T), at_risk(T), fix(T), affirms_affection(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("fragile", tid))
        lines.append(asp.fact("stored_on", tid, t.region))
    for g in GEAR:
        lines.append(asp.fact("tool", g.id))
        for f in g.fixes:
            lines.append(asp.fact("solves", g.id, f))
            lines.append(asp.fact("matches", g.id, f))
    lines.append(asp.fact("chosen", "repair"))
    lines.append(asp.fact("trouble_of", "repair", "tat"))
    lines.append(asp.fact("disturbs", "repair", "chest"))
    lines.append(asp.fact("affirms_affection", "tat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TREASURES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with affectionate inner-monologue conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name", choices=PIRATE_NAMES)
    ap.add_argument("--role", choices=MATES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    name = args.name or rng.choice(PIRATE_NAMES)
    role = args.role or rng.choice(MATES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, treasure=treasure, name=name, role=role, trait=trait)


def _do_repair(world: World, pirate: Entity, treasure: Entity, gear: Gear) -> None:
    pirate.memes["conflict"] = 0
    pirate.memes["affection"] = pirate.memes.get("affection", 0) + 1
    treasure.meters["repaired"] = 1
    world.say(
        f"At last, {pirate.id} chose the kind way. With {gear.label}, {pirate.pronoun('subject')} "
        f"{gear.prep}, and the tat was safe again."
    )
    world.say(
        f"{gear.tail}, and {pirate.id} smiled at the tiny keepsake as the ship rocked softly by the harbor."
    )


def tell(setting: Setting, treasure_cfg: Treasure, params: StoryParams) -> World:
    world = World(setting)
    pirate = world.add(Entity(id=params.name, kind="character", type="captain" if params.role == "captain" else "mate"))
    mate = world.add(Entity(id="Mate", kind="character", type="mate", label=params.role))
    treasure = world.add(Entity(
        id="Treasure",
        kind="thing",
        type="treasure",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=pirate.id,
        caretaker=mate.id,
    ))

    world.say(f"{pirate.id} was an {params.trait} little pirate who sailed with {mate.label or params.role}.")
    world.say(f"{pirate.id} kept {pirate.pronoun('possessive')} {treasure.label} close, because it was {treasure_cfg.value}.")
    pirate.memes["love"] = 1
    pirate.memes["affection"] = 1

    world.para()
    world.say(
        f"One morning at {setting.place}, {pirate.id} found that the old {treasure.label} had a torn edge."
    )
    world.say(
        f"{pirate.id} wanted to sail right away, but {pirate.pronoun('possessive')} chest felt tight with worry."
    )
    world.say(
        f"In {pirate.pronoun('possessive')} head, {pirate.id} thought, "
        f"'{pirate.id} can be bold and still care. A pirate does not have to choose between adventure and love.'"
    )
    pirate.memes["conflict"] = 1
    pirate.memes["worry"] = 1

    world.para()
    world.say(
        f"{mate.label or params.role} noticed the torn edge and frowned. "
        f"\"If we leave it, the {treasure.label} may get worse,\" {mate.pronoun('subject')} said."
    )
    world.say(
        f"{pirate.id} bit {pirate.pronoun('possessive')} lip, and the wind rattled the ropes."
    )
    world.say(
        f"In {pirate.pronoun('possessive')} own thoughts, {pirate.id} felt the tug of a hard choice: keep sailing, or pause and mend."
    )

    world.para()
    gear = GEAR[0] if treasure_cfg.label == "tat" else GEAR[1]
    world.say(
        f"Then {pirate.id} lifted {gear.label} from a small chest and nodded."
    )
    world.say(
        f"\"Let's fix it first,\" {pirate.id} said softly, because {pirate.pronoun('subject')} loved the little keepsake too much to rush."
    )
    _do_repair(world, pirate, treasure, gear)

    world.facts.update(pirate=pirate, mate=mate, treasure=treasure, gear=gear, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short pirate tale about {f['pirate'].id}, an {f['params'].trait']} pirate, who feels an affectionate worry over a tat.",
        f"Tell a child-friendly story set at {f['setting'].place} where a pirate's inner monologue turns a conflict into a gentle repair.",
        f"Write a pirate story that includes the word 'tat' and ends with a repaired keepsake and a calmer heart.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pirate = f["pirate"]
    mate = f["mate"]
    treasure = f["treasure"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the pirate worried about the torn {treasure.label}?",
            answer=f"{pirate.id} was worried, because {pirate.pronoun('subject')} loved the old {treasure.label} and did not want it to get worse."
        ),
        QAItem(
            question=f"What did {pirate.id} think in {pirate.pronoun('possessive')} own mind before making a choice?",
            answer=f"{pirate.id} thought that {pirate.pronoun('subject')} could be brave and still care, so {pirate.pronoun('subject')} did not have to choose between sailing and affection."
        ),
        QAItem(
            question=f"How did {pirate.id} and {mate.label or 'the mate'} fix the tat?",
            answer=f"They used {gear.label} to mend it first, and then the little tat stayed safe while they stayed together."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tat?", answer="A tat is a small old piece of cloth or trim, often worn thin, torn, or faded from use."),
        QAItem(question="What is a harbor?", answer="A harbor is a safe place near the water where ships can stop and rest."),
        QAItem(question="What does affectionate mean?", answer="Affectionate means warm and caring, like when someone shows gentle love."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TREASURES[params.treasure], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"WQ: {item.question}")
            print(f"WA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for treasure in TREASURES:
                params = StoryParams(place=place, treasure=treasure, name=PIRATE_NAMES[0], role=MATES[0], trait=TRAITS[0], seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
