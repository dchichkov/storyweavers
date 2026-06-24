#!/usr/bin/env python3
"""
storyworlds/worlds/dopey_rib_shape_mystery_to_solve_humor.py
=============================================================

A small myth-style story world about a dopey hero, a strange rib-shaped clue,
and a mystery that can be solved with a little humor, a little courage, and a
clear ending image.

Premise:
- A clumsy but kind character keeps finding signs of a missing "shape".
- The shape is tied to a rib-shaped relic, a carved arch, or a moon-shadow
  depending on the setting.
- The hero worries the village will laugh, but the worry itself becomes the key
  to solving the mystery.

The world is intentionally tiny and constraint-checked:
- physical meters track locations, possession, and clue-state
- emotional memes track confusion, pride, relief, and laughter
- the story turns when the hero notices the joke hidden in the clue
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"hero", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type in {"girl", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sky: str
    mystery_source: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    shape: str
    hint: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    witness: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "hill": Setting(
        place="the hill temple",
        sky="moonlit",
        mystery_source="the old stone altar",
        affords={"moon", "shadow"},
    ),
    "cave": Setting(
        place="the echo cave",
        sky="dim",
        mystery_source="the rib gate",
        affords={"echo", "shadow"},
    ),
    "river": Setting(
        place="the river shrine",
        sky="bright",
        mystery_source="the water reeds",
        affords={"reflection", "shadow"},
    ),
}

CLUES = {
    "rib": Clue(
        id="rib",
        label="a rib-shaped relic",
        phrase="a strange rib-shaped relic",
        shape="rib",
        hint="It curved like a half-moon and looked a little like a spoon for giants.",
        reveal="the relic was part of an old arch",
        tags={"rib", "shape"},
    ),
    "shape": Clue(
        id="shape",
        label="a broken shape-mark",
        phrase="a broken shape-mark carved in stone",
        shape="shape",
        hint="Its edges made a funny outline, as if someone had drawn the idea of a shape instead of the shape itself.",
        reveal="the mark was a map clue",
        tags={"shape"},
    ),
    "dopey_rib": Clue(
        id="dopey_rib",
        label="a dopey rib charm",
        phrase="a dopey rib charm with a lopsided grin",
        shape="rib",
        hint="The charm had a crooked grin, like it knew a joke before anyone else did.",
        reveal="the charm fit into a hidden notch",
        tags={"dopey", "rib", "shape"},
    ),
}

GENDER_NAMES = {
    "girl": ["Mira", "Nia", "Lina", "Iris", "Tala"],
    "boy": ["Ari", "Bram", "Kian", "Milo", "Soren"],
}

TRAITS = ["dopey", "earnest", "curious", "gentle", "bouncy"]
WITNESSES = ["priest", "elder", "owl", "goat", "child"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def _m(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _e(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def reasonableness_gate(setting: Setting, clue: Clue) -> bool:
    if setting.place == "the hill temple":
        return True
    if setting.place == "the echo cave":
        return clue.shape in {"rib", "shape"}
    if setting.place == "the river shrine":
        return clue.shape in {"shape", "rib"}
    return False


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            if reasonableness_gate(setting, clue):
                out.append((place, clue_id))
    return out


def introduce(world: World, hero: Entity, clue: Clue) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a little {hero.memes.get('trait', 'dopey')} seeker who loved old stories and odd questions."
    )
    world.say(
        f"One day {hero.id} found {clue.phrase}, and everyone said it looked important."
    )


def mystery_begins(world: World, hero: Entity, clue: Clue, witness: Entity) -> None:
    _e(hero, "curiosity", 1)
    _e(hero, "confusion", 1)
    _m(hero, "clue_close", 1)
    world.say(
        f"{hero.id} carried {clue.it()} to {witness.label}, but the witness only squinted and said, "
        f'"It is a mystery, and mysteries can be funny."'
    )
    world.say(
        f"{hero.id} frowned at the clue, because it was shaped like a joke he could not yet hear."
    )


def mishap(world: World, hero: Entity, clue: Clue) -> None:
    _e(hero, "dopey", 1)
    _e(hero, "embarrassment", 1)
    world.say(
        f"When {hero.id} tried to hold {clue.it()} up to the light, {hero.pronoun()} dropped it in a bowl of figs."
    )
    world.say(
        f"The figs rolled everywhere, which made the priests laugh, and the laughter sounded kindly instead of cruel."
    )
    _e(hero, "laughter", 1)


def insight(world: World, hero: Entity, clue: Clue, witness: Entity) -> None:
    _e(hero, "joy", 1)
    _e(hero, "understanding", 1)
    world.say(
        f"Then {hero.id} noticed the joke hidden in the mystery: {clue.hint}"
    )
    world.say(
        f"{hero.id} laughed too, and {witness.label} nodded as if the answer had been waiting behind the smile all along."
    )


def resolve(world: World, hero: Entity, clue: Clue) -> None:
    _e(hero, "relief", 1)
    _e(hero, "pride", 1)
    world.say(
        f"{hero.id} turned {clue.it()} around and found the truth: {clue.reveal}."
    )
    world.say(
        f"So the strange shape was not a trouble at all. It was a useful old piece of the world, and {hero.id} had solved it by being a little dopey and a lot careful."
    )


def tell(setting: Setting, clue: Clue, hero_name: str, hero_type: str, witness_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    witness = world.add(Entity(id="Witness", kind="character", type=witness_type, label=f"the {witness_type}"))
    relic = world.add(Entity(
        id="Clue",
        type="thing",
        label=clue.label,
        phrase=clue.phrase,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, witness=witness, clue=relic, clue_cfg=clue, setting=setting)
    introduce(world, hero, clue)
    world.para()
    mystery_begins(world, hero, clue, witness)
    mishap(world, hero, clue)
    world.para()
    insight(world, hero, clue, witness)
    resolve(world, hero, clue)
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue_cfg"]
    setting: Setting = f["setting"]
    return [
        f'Write a short myth about {hero.id} and a mysterious {clue.shape}-shaped clue in {setting.place}.',
        f"Tell a child-friendly story where a dopey seeker laughs at a mystery and then solves it.",
        f'Write a myth-style story that uses the words "dopey", "{clue.shape}", and "shape" naturally.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    clue: Clue = f["clue_cfg"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, a little dopey seeker who carried {clue.it()} to the {witness.label}.",
        ),
        QAItem(
            question=f"What strange thing did {hero.id} find?",
            answer=f"{hero.id} found {clue.phrase}, which looked important and a little silly at the same time.",
        ),
        QAItem(
            question=f"Why did the story feel funny before the answer came?",
            answer=f"It felt funny because {hero.id} was dopey, dropped {clue.it()} in figs, and everyone laughed kindly before the mystery was solved.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was that {clue.reveal}. That is why the odd shape belonged in the story after all.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rib-shaped thing?",
            answer="A rib-shaped thing is long and curved, like part of a cage or an arch, and it can make people wonder what it belongs to.",
        ),
        QAItem(
            question="What does shape mean?",
            answer="A shape is the outline or form of something, like a circle, a line, or the curve of a bone.",
        ),
        QAItem(
            question="Why can a mystery be funny?",
            answer="A mystery can be funny when the answer is surprising, when someone makes a harmless mistake, or when the clue looks sillier than expected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8} {e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, clue: Clue) -> str:
    return f"(No story: {clue.phrase} does not fit the mythic mystery at {setting.place}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, setting.place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("shape", cid, clue.shape))
        for t in sorted(clue.tags):
            lines.append(asp.fact("tag", cid, t))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, C) :- setting(S), clue(C), shape(C, rib), affords(S, shadow).
compatible(S, C) :- setting(S), clue(C), shape(C, shape).
compatible(S, C) :- setting(S), clue(C), shape(C, rib).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic dopey rib-shape mystery story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--witness", choices=WITNESSES)
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
    combos = valid_combos()
    if args.place and args.clue:
        if (args.place, args.clue) not in combos:
            raise StoryError(explain_rejection(SETTINGS[args.place], CLUES[args.clue]))
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    witness = args.witness or rng.choice(WITNESSES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue_id, name=name, gender=gender, witness=witness, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.name, params.gender, params.witness, params.trait)
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
    StoryParams(place="hill", clue="rib", name="Mira", gender="girl", witness="owl", trait="dopey"),
    StoryParams(place="cave", clue="shape", name="Ari", gender="boy", witness="elder", trait="curious"),
    StoryParams(place="river", clue="dopey_rib", name="Tala", gender="girl", witness="priest", trait="earnest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for place, clue in combos:
            print(f"  {place:8} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
