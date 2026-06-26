#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/amorphous_garage_crowded_market_misunderstanding_fable.py
===============================================================================================================================

A compact fable-style story world about an amorphous helper, a crowded market,
and a misunderstanding that clears when someone looks more closely.

Premise:
- A small amorphous creature lives near a garage at the edge of a crowded market.
- It wants to help carry and sort market goods.
- In the crush of people, its shapeless form makes others fear it is causing trouble.

Turn:
- The marketkeeper mistakes the creature for a thief or spill.
- Confusion rises; the crowd copies the worry.

Resolution:
- The creature calmly shows the real job it was doing.
- The misunderstanding fades, trust grows, and the market learns a fable-like lesson:
  do not judge by appearance alone.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the crowded market"
    afford_misunderstanding: bool = True
    afford_helping: bool = True


@dataclass
class Role:
    id: str
    type: str
    label: str
    phrase: str
    trait: str
    emotional_start: str
    emotional_end: str


@dataclass
class StoryParams:
    role: str = "helper"
    name: str = "Milo"
    witness: str = "merchant"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


ROLES = {
    "helper": Role(
        id="helper",
        type="amorphous",
        label="the amorphous helper",
        phrase="an amorphous helper from the garage",
        trait="gentle",
        emotional_start="hopeful",
        emotional_end="trusted",
    ),
    "child": Role(
        id="child",
        type="boy",
        label="a little child",
        phrase="a curious child from the garage",
        trait="curious",
        emotional_start="hopeful",
        emotional_end="confident",
    ),
}

WITNESSES = {
    "merchant": {"type": "merchant", "label": "the market merchant"},
    "seller": {"type": "seller", "label": "the fruit seller"},
    "guard": {"type": "guard", "label": "the gate guard"},
}

SETTINGS = {
    "crowded_market": Setting(place="the crowded market", afford_misunderstanding=True, afford_helping=True),
}

MORAL = "Do not judge a helper by the shape of its shadow."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: an amorphous helper, a crowded market, and a misunderstanding."
    )
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--name")
    ap.add_argument("--witness", choices=WITNESSES)
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
    role = args.role or rng.choice(list(ROLES))
    witness = args.witness or rng.choice(list(WITNESSES))
    name = args.name or rng.choice(["Milo", "Nori", "Pip", "Arlo", "Tavi"])
    return StoryParams(role=role, name=name, witness=witness)


def reasonableness_gate(params: StoryParams) -> None:
    if params.role not in ROLES:
        raise StoryError("Unknown role.")
    if params.witness not in WITNESSES:
        raise StoryError("Unknown witness.")
    if params.role == "helper" and not params.name:
        raise StoryError("The helper needs a name.")


def tell_story(params: StoryParams) -> World:
    role = ROLES[params.role]
    witness = WITNESSES[params.witness]
    world = World(SETTINGS["crowded_market"])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=role.type,
        label=role.label,
        phrase=role.phrase,
        traits=[role.trait, "small"],
        meters={"carried_load": 0.0, "bump": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "trust": 0.0, "confusion": 0.0, "relief": 0.0},
    ))
    witness_ent = world.add(Entity(
        id="Witness",
        kind="character",
        type=witness["type"],
        label=witness["label"],
        phrase=witness["label"],
        meters={"attention": 1.0},
        memes={"worry": 0.0, "trust": 0.0, "confusion": 0.0, "relief": 0.0},
    ))
    garage = world.add(Entity(
        id="Garage",
        kind="thing",
        type="garage",
        label="the old garage",
        phrase="an old garage beside the market",
        owner=params.name,
    ))
    basket = world.add(Entity(
        id="Basket",
        kind="thing",
        type="basket",
        label="a basket of pears",
        phrase="a basket of pears",
        caretaker=witness_ent.id,
        carries=["pears"],
        meters={"safe": 1.0},
    ))

    world.say(
        f"Near the crowded market stood {garage.phrase}. {hero.id} lived there and "
        f"liked to help when the stalls were busiest."
    )
    world.say(
        f"{hero.id} was {role.emotional_start} because {hero.pronoun('subject')} had promised to carry "
        f"{basket.phrase} to {witness_ent.label} without dropping a single pear."
    )

    world.para()
    hero.meters["carried_load"] += 1.0
    world.say(
        f"When the noon crowd pressed in, {hero.id} squeezed between baskets and boots, "
        f"careful and slow."
    )
    hero.meters["bump"] += 1.0
    witness_ent.memes["confusion"] += 1.0
    world.say(
        f"But the market was so packed that {witness_ent.label} saw only a wobbly shape in the crowd "
        f"and cried, 'Stop! That shapeless thing is upsetting the stand!'"
    )
    hero.memes["worry"] += 1.0
    witness_ent.memes["worry"] += 1.0
    world.say(
        f"{hero.id} froze. {hero.pronoun('subject').capitalize()} had not meant any harm at all, "
        f"only to help."
    )

    world.para()
    witness_ent.memes["confusion"] += 1.0
    world.say(
        f"People turned to stare. Some guessed {hero.id} was a spill, and some guessed {hero.id} was a thief, "
        f"because the crowd had not seen the basket."
    )
    world.say(
        f"Then {hero.id} gently lifted {basket.phrase} high enough for everyone to see."
    )
    witness_ent.memes["trust"] += 1.0
    witness_ent.memes["worry"] = 0.0
    world.say(
        f"'I came from the garage to help,' {hero.id} said. 'I was only keeping the pears safe.'"
    )
    world.say(
        f"The marketkeeper looked again, blinked, and understood. The misunderstanding melted away like ice in sun."
    )

    world.para()
    hero.memes["relief"] += 1.0
    hero.memes["trust"] += 1.0
    witness_ent.memes["relief"] += 1.0
    world.say(
        f"{witness_ent.label} smiled, thanked {hero.id}, and set the pears in order. "
        f"{hero.id} felt {role.emotional_end}, and the crowd made room at last."
    )
    world.say(
        f"From then on, the merchant told the children of the market a little fable: "
        f"'{MORAL}'"
    )

    world.facts.update(
        hero=hero,
        witness=witness_ent,
        garage=garage,
        basket=basket,
        role=role,
        setting=world.setting,
        moral=MORAL,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    witness = f["witness"]
    return [
        "Write a short fable for children set in a crowded market where an amorphous helper is misunderstood, then cleared.",
        f"Tell a gentle story in which {hero.id} helps {witness.label} near a garage at the edge of a crowded market.",
        "Write a tiny moral tale about a shapeless creature, a busy market, and the lesson that appearances can deceive.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    witness = f["witness"]
    basket = f["basket"]
    return [
        QAItem(
            question=f"Why did {witness.label} first get upset at {hero.id} in the market?",
            answer=(
                f"{witness.label} got upset because the market was crowded and {hero.id} looked like a wobbly shapeless blur. "
                f"{witness.label} could not see that {hero.id} was carrying {basket.phrase} carefully."
            ),
        ),
        QAItem(
            question=f"What was {hero.id} really trying to do near the garage and the market stalls?",
            answer=(
                f"{hero.id} was really trying to help by carrying {basket.phrase} safely from the garage side of the market. "
                f"{hero.id} was not causing trouble at all."
            ),
        ),
        QAItem(
            question=f"What changed after {hero.id} lifted the basket up?",
            answer=(
                f"Once {hero.id} lifted {basket.phrase} high enough to see, the misunderstanding faded. "
                f"{witness.label} understood the help, the worry went away, and the crowd made room."
            ),
        ),
        QAItem(
            question="What moral does the story teach?",
            answer=MORAL,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garage?",
            answer="A garage is a building or shelter used to store vehicles, tools, or working things safely out of the weather.",
        ),
        QAItem(
            question="What does it mean to misunderstand someone?",
            answer="To misunderstand someone means to think they mean one thing when they actually mean something different.",
        ),
        QAItem(
            question="What is a market?",
            answer="A market is a place where people buy and sell food and other goods.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carries:
            bits.append(f"carries={e.carries}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(role="helper", name="Milo", witness="merchant"),
    StoryParams(role="helper", name="Nori", witness="seller"),
    StoryParams(role="helper", name="Pip", witness="guard"),
]


ASP_RULES = r"""
% A story is valid when it uses the crowded market setting and a misunderstanding.
valid_story(S, R, W) :- setting(S), role(R), witness(W), crowded(S), misunderstand(R), market(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "crowded" in sid:
            lines.append(asp.fact("crowded", sid))
        if "market" in sid:
            lines.append(asp.fact("market", sid))
    for rid, r in ROLES.items():
        lines.append(asp.fact("role", rid))
        lines.append(asp.fact("type", rid, r.type))
        lines.append(asp.fact("misunderstand", rid))
    for wid in WITNESSES:
        lines.append(asp.fact("witness", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(sid, rid, wid) for sid in SETTINGS for rid in ROLES for wid in WITNESSES}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_story_from_params(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.role} near the crowded market"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
