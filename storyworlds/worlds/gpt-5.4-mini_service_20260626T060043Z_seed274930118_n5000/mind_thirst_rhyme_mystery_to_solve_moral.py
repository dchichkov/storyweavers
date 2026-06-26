#!/usr/bin/env python3
"""
A standalone storyworld: a small space-adventure mystery about a thirsty mind,
a rhyme clue, and a moral choice.

Premise:
- A young crew member on a tiny starship feels thirst and worry.
- A missing water vial creates a mystery to solve.
- Clues arrive as short rhymes.
- The resolution proves a moral value: share, tell the truth, and help others.

The world is state-driven:
- meters track thirst, water, attention, and clue progress.
- memes track worry, courage, relief, and trust.
- the story changes according to what the crew learns and chooses.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["thirst", "water", "clue", "anxiety", "trust", "relief", "courage", "guilt"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str = "the Star Moth"
    location: str = "between bright moons and a blue comet"
    rhyme_style: str = "short"


@dataclass
class World:
    ship: Ship
    entities: dict[str, Entity] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    mentor_name: str
    mystery: str
    moral: str
    seed: Optional[int] = None


HEROES = [
    ("Nova", "girl"),
    ("Pip", "boy"),
    ("Rio", "boy"),
    ("Luna", "girl"),
    ("Zed", "boy"),
    ("Mira", "girl"),
]

MENTORS = ["Captain Sol", "Aunt Vega", "Pilot Quill", "Doctor Comet"]
MYSTERIES = [
    "the missing water vial",
    "the silent recycler",
    "the empty cup in the cabin",
]
MORALS = [
    "share what you have",
    "tell the truth right away",
    "help the crew before blaming anyone",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure mystery about thirst, rhyme clues, and a moral choice."
    )
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--mentor-name", choices=MENTORS)
    ap.add_argument("--mystery", choices=["vial", "recycler", "cup"])
    ap.add_argument("--moral", choices=["share", "truth", "help"])
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
    hero_name, hero_type = rng.choice(HEROES)
    mentor_name = rng.choice(MENTORS)
    mystery = rng.choice(["vial", "recycler", "cup"])
    moral = rng.choice(["share", "truth", "help"])

    if args.hero_type:
        hero_name, hero_type = next((n, t) for n, t in HEROES if t == args.hero_type)
    if args.hero_name:
        hero_name = args.hero_name
    if args.mentor_name:
        mentor_name = args.mentor_name
    if args.mystery:
        mystery = args.mystery
    if args.moral:
        moral = args.moral

    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        mentor_name=mentor_name,
        mystery=mystery,
        moral=moral,
    )


def rhyme_clue(mystery: str) -> str:
    return {
        "vial": "Find the trail where the small blue vial fell while the moonlight was pale.",
        "recycler": "If the recycler rests, check the nest near the vents and the west-side mesh.",
        "cup": "The cup did not hop; look by the map dock and the snack block.",
    }[mystery]


def moral_line(moral: str) -> str:
    return {
        "share": "A full heart can share a small cup.",
        "truth": "A brave mouth can tell the truth.",
        "help": "A kind hand can help first and ask later.",
    }[moral]


def clue_answer(mystery: str) -> str:
    return {
        "vial": "The missing water vial had rolled under the navigation seat.",
        "recycler": "The silent recycler was only clogged with a tiny foil wrapper.",
        "cup": "The empty cup had been carried to the plant bay and left beside the sprouts.",
    }[mystery]


def generate_world(params: StoryParams) -> World:
    ship = Ship()
    world = World(ship=ship)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type="captain",
        label=params.mentor_name,
    ))
    object_label = {
        "vial": "water vial",
        "recycler": "recycler",
        "cup": "cup",
    }[params.mystery]
    mystery_obj = world.add(Entity(
        id="mystery",
        type="thing",
        label=object_label,
        phrase=f"the {object_label}",
        owner=hero.id,
    ))

    hero.meters["thirst"] = 1.0
    hero.memes["anxiety"] = 1.0
    mentor.memes["trust"] = 1.0

    world.say(
        f"{hero.label} floated through {ship.name}, feeling a dry tickle in {hero.pronoun('possessive')} throat."
    )
    world.say(
        f"{hero.label} wanted to think clearly, but {hero.pronoun('possessive')} mind felt foggy from thirst."
    )
    world.say(
        f"Then {mentor.label} said the ship had a mystery to solve: {mystery_obj.phrase} was missing or not working."
    )

    world.para()
    world.say(
        f"A tiny rhyme drifted from the wall speaker: \"{rhyme_clue(params.mystery)}\""
    )
    hero.meters["clue"] = 1.0
    hero.memes["courage"] += 1.0
    world.say(
        f"{hero.label} took a slow breath. A calm mind could follow a rhyme, step by step."
    )

    if params.mystery == "vial":
        world.say("The clues led past the map room and down to the navigation seat.")
    elif params.mystery == "recycler":
        world.say("The clues led to the recycler bay, where the machine hummed but stayed dry and quiet.")
    else:
        world.say("The clues led to the plant bay, where small leaves nodded beside the storage bins.")

    world.para()
    world.say(clue_answer(params.mystery))
    hero.memes["relief"] += 1.0
    hero.meters["thirst"] = 0.0
    mystery_obj.memes["trust"] += 1.0

    if params.moral == "share":
        world.say(
            f"{hero.label} shared the recovered water with the crew, and no one had to feel left out."
        )
    elif params.moral == "truth":
        world.say(
            f"{hero.label} told the truth at once, and that honesty helped the whole ship breathe easier."
        )
    else:
        world.say(
            f"{hero.label} helped fix the problem first, and the crew learned that kindness can move faster than blame."
        )

    world.say(
        f"At the end, {hero.label} sipped cool water and smiled, with {mentor.label} beside {hero.pronoun('object')} and the stars shining steady outside."
    )

    world.facts.update(
        hero=hero,
        mentor=mentor,
        mystery=params.mystery,
        moral=params.moral,
        mystery_obj=mystery_obj,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short space-adventure story for a young child about {hero.label}, thirst, and a mystery to solve.',
        f'Tell a gentle story where {hero.label} follows a rhyme clue on a starship and learns a moral value.',
        f'Create a child-friendly mystery story with a calm ending image, using the word "mind" and the word "thirst".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    mystery = f["mystery"]
    moral = f["moral"]
    obj = f["mystery_obj"]

    return [
        QAItem(
            question=f"Why was {hero.label} having trouble thinking clearly at the start of the story?",
            answer=f"{hero.label} felt thirst in {hero.pronoun('possessive')} body, and that made {hero.pronoun('possessive')} mind foggy."
        ),
        QAItem(
            question=f"What mystery did {mentor.label} ask {hero.label} to solve?",
            answer=f"{mentor.label} asked {hero.label} to solve the mystery of {obj.phrase}."
        ),
        QAItem(
            question="What clue helped the search move forward?",
            answer=f"A short rhyme helped the search move forward: {rhyme_clue(mystery)}"
        ),
        QAItem(
            question="What good choice did the hero make at the end?",
            answer={
                "share": "The hero shared the water with the crew.",
                "truth": "The hero told the truth right away.",
                "help": "The hero helped fix the problem before blaming anyone.",
            }[moral],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is thirst?",
            answer="Thirst is the feeling that tells your body it needs water."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bright and night."
        ),
        QAItem(
            question="Why is telling the truth a moral value?",
            answer="Telling the truth is a moral value because it helps people trust one another and make fair choices."
        ),
    ]


ASP_RULES = r"""
hero_thirsty(H) :- hero(H), thirsty(H).
mind_foggy(H) :- hero_thirsty(H), not relieved(H).
clue_helpful(C) :- rhyme(C).
mystery_solved(M) :- mystery(M), clue_helpful(_), found(M).
moral_choice(H, share) :- hero(H), shared(H).
moral_choice(H, truth) :- hero(H), told_truth(H).
moral_choice(H, help) :- hero(H), helped(H).
valid_story(H, M, Moral) :- hero(H), mystery(M), moral(Moral).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("thirsty", "hero"),
            asp.fact("mystery", "vial"),
            asp.fact("mystery", "recycler"),
            asp.fact("mystery", "cup"),
            asp.fact("rhyme", "clue1"),
            asp.fact("found", "vial"),
            asp.fact("relieved", "hero"),
            asp.fact("shared", "hero"),
            asp.fact("told_truth", "hero"),
            asp.fact("helped", "hero"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("hero", "vial", "share"), ("hero", "recycler", "share"), ("hero", "cup", "share"),
                ("hero", "vial", "truth"), ("hero", "recycler", "truth"), ("hero", "cup", "truth"),
                ("hero", "vial", "help"), ("hero", "recycler", "help"), ("hero", "cup", "help")}
    if atoms == expected:
        print(f"OK: ASP parity check passed ({len(atoms)} valid_story atoms).")
        return 0
    print("MISMATCH in ASP parity check")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.label or ent.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def resolve_params_for_all() -> list[StoryParams]:
    return [
        StoryParams("Nova", "girl", "Captain Sol", "vial", "share"),
        StoryParams("Pip", "boy", "Pilot Quill", "recycler", "truth"),
        StoryParams("Luna", "girl", "Doctor Comet", "cup", "help"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in resolve_params_for_all():
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            p = resolve_params(args, rng)
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
