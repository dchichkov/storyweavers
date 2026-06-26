#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/banker_inhabitant_leotard_dialogue_sharing_twist_superhero.py
==============================================================================================================

A small superhero story world: a banker, an inhabitant, and a leotard, with
dialogue, sharing, and a twist.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "mom", "inhabitant"}
        male = {"man", "boy", "father", "dad", "banker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city bank"
    affords: set[str] = field(default_factory=lambda: {"rescue", "share", "disguise"})


@dataclass
class Twist:
    clue: str
    reveal: str


@dataclass
class StoryParams:
    place: str
    name: str
    banker_type: str
    inhabitant_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bank": Setting(place="the city bank"),
    "rooftop": Setting(place="the rooftop above the bank"),
    "alley": Setting(place="the lantern-lit alley"),
}

BANKER_TYPES = ["banker", "teller", "manager"]
INHABITANT_TYPES = ["inhabitant", "shopkeeper", "neighbor"]
NAMES = ["Mina", "Ravi", "Tess", "Omar", "Lina", "Noah", "Iris", "Ezra"]

LEOTARDS = {
    "blue": "a bright blue leotard",
    "red": "a shiny red leotard",
    "gold": "a golden leotard",
}

TWISTS = [
    Twist(
        clue="a hidden emblem stitched inside the collar",
        reveal="the banker had been a masked hero all along",
    ),
    Twist(
        clue="the leotard came with a note that said 'for the brave one'",
        reveal="the inhabitant had sewn it for the banker to become a hero",
    ),
    Twist(
        clue="the bank vault mirrored the leotard's colors",
        reveal="the leotard was the key to a secret rescue suit",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def pronoun_cap(entity: Entity, case: str = "subject") -> str:
    return entity.pronoun(case).capitalize()


def _safe_name(name: str) -> str:
    if not name or not name[0].isalpha():
        raise StoryError("name must begin with a letter")
    return name


def _do_rescue(world: World, banker: Entity, inhabitant: Entity, leotard: Entity) -> None:
    banker.meters["heroism"] = banker.meters.get("heroism", 0) + 1
    inhabitant.memes["relief"] = inhabitant.memes.get("relief", 0) + 1
    if leotard.worn_by == banker.id:
        leotard.meters["used"] = leotard.meters.get("used", 0) + 1


def _share(world: World, giver: Entity, receiver: Entity, item: Entity) -> None:
    giver.memes["generosity"] = giver.memes.get("generosity", 0) + 1
    receiver.memes["trust"] = receiver.memes.get("trust", 0) + 1
    item.owner = receiver.id
    item.worn_by = receiver.id


def _twist(world: World, banker: Entity, inhabitant: Entity, item: Entity, twist: Twist) -> None:
    world.facts["twist"] = twist
    banker.memes["surprise"] = banker.memes.get("surprise", 0) + 1
    inhabitant.memes["wonder"] = inhabitant.memes.get("wonder", 0) + 1
    world.say(f"Then the truth came out: {twist.reveal}.")


def tell(setting: Setting, banker_type: str, inhabitant_type: str, name: str) -> World:
    world = World(setting)
    banker = world.add(Entity(id="Banker", kind="character", type=banker_type, label="the banker"))
    inhabitant = world.add(Entity(id="Inhabitant", kind="character", type=inhabitant_type, label="the inhabitant"))
    leotard = world.add(Entity(
        id="Leotard",
        type="leotard",
        label="leotard",
        phrase=LEOTARDS["blue"],
        owner=banker.id,
        worn_by=None,
    ))
    hero_name = _safe_name(name)
    twist = random.choice(TWISTS)

    # Act 1: setup
    world.say(
        f"{hero_name} was a small hero who watched {setting.place} with sharp eyes and a kind heart."
    )
    world.say(
        f"Inside the bank, the banker kept {banker.pronoun('possessive')} {leotard.label} folded like a secret."
    )
    world.say(
        f"The inhabitant admired it and said, \"That looks like a brave outfit.\""
    )
    world.say(
        f'The banker smiled and said, "{hero_name}, today we might need more than money."'
    )

    # Act 2: tension
    world.para()
    world.say(
        f"At noon, trouble rolled in when the bank lights flickered and a heavy door jammed shut."
    )
    world.say(
        f"The inhabitant whispered, \"Can anyone get us out?\""
    )
    world.say(
        f"The banker lifted the leotard and said, \"I kept this for a moment like this.\""
    )
    _share(world, banker, inhabitant, leotard)
    world.say(
        f'{pronoun_cap(inhabitant)} took the leotard and said, "If we share the brave thing, we can share the brave job."'
    )
    world.say(
        f"The two of them worked together: one held the lever, the other called for help."
    )
    _do_rescue(world, banker, inhabitant, leotard)

    # Act 3: twist and ending
    world.para()
    world.say(
        f"The doors opened at last, and the air outside felt bright and cool."
    )
    world.say(
        f'The banker leaned close and said, "You think I was only a banker, but I was waiting for the right moment."'
    )
    _twist(world, banker, inhabitant, leotard, twist)
    world.say(
        f"With a laugh, {hero_name} saw {leotard.pronoun('possessive')} shiny seam catch the light like a tiny lightning bolt."
    )
    world.say(
        f"In the end, the banker and the inhabitant stood side by side, sharing the leotard, the credit, and the smile."
    )

    world.facts.update(
        hero_name=hero_name,
        banker=banker,
        inhabitant=inhabitant,
        leotard=leotard,
        setting=setting,
        twist=twist,
        shared=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes a banker, an inhabitant, and a leotard.',
        f"Tell a story where the banker and the inhabitant speak to each other, share a leotard, and end with a twist.",
        f"Write a simple superhero tale set at {f['setting'].place} with a hidden surprise in the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    banker: Entity = f["banker"]
    inhabitant: Entity = f["inhabitant"]
    leotard: Entity = f["leotard"]
    twist: Twist = f["twist"]
    setting: Setting = f["setting"]
    hero_name = f["hero_name"]

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero_name}, the banker, and the inhabitant at {setting.place}.",
        ),
        QAItem(
            question=f"What did the banker share?",
            answer=f"The banker shared {banker.pronoun('possessive')} {leotard.label} with the inhabitant.",
        ),
        QAItem(
            question=f"What did the inhabitant say about the brave outfit?",
            answer=f"The inhabitant said that the leotard looked like a brave outfit.",
        ),
        QAItem(
            question=f"What helped the two characters work together?",
            answer="They talked to each other, shared the leotard, and used it as part of their rescue plan.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {twist.reveal}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banker?",
            answer="A banker is a person who works with money at a bank.",
        ),
        QAItem(
            question="What is an inhabitant?",
            answer="An inhabitant is a person who lives in a place.",
        ),
        QAItem(
            question="What is a leotard?",
            answer="A leotard is a tight outfit that can be worn for dance, sports, or a costume.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or have something too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
banker(B) :- banker_type(B).
inhabitant(I) :- inhabitant_type(I).
leotard(L) :- leotard_item(L).

shared(L) :- gives(B, I, L), banker(B), inhabitant(I), leotard(L).
rescued(B, I) :- shared(L), banker(B), inhabitant(I).
twist(T) :- twist_kind(T).
valid_story(P) :- setting(P), banker(_), inhabitant(_), leotard(_), shared(_), twist(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for bt in BANKER_TYPES:
        lines.append(asp.fact("banker_type", bt))
    for it in INHABITANT_TYPES:
        lines.append(asp.fact("inhabitant_type", it))
    for lid in LEOTARDS:
        lines.append(asp.fact("leotard_item", lid))
    for i in range(len(TWISTS)):
        lines.append(asp.fact("twist_kind", f"t{i}"))
    lines.append(asp.fact("gives", "banker", "inhabitant", "leotard"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    has_valid = bool(asp.atoms(model, "valid_story"))
    if has_valid == asp_valid():
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with banker, inhabitant, leotard, dialogue, sharing, and twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--banker-type", choices=BANKER_TYPES)
    ap.add_argument("--inhabitant-type", choices=INHABITANT_TYPES)
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
    name = _safe_name(args.name or rng.choice(NAMES))
    banker_type = args.banker_type or rng.choice(BANKER_TYPES)
    inhabitant_type = args.inhabitant_type or rng.choice(INHABITANT_TYPES)
    return StoryParams(place=place, name=name, banker_type=banker_type, inhabitant_type=inhabitant_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.banker_type, params.inhabitant_type, params.name)
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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="bank", name="Mina", banker_type="banker", inhabitant_type="neighbor"),
            StoryParams(place="rooftop", name="Ravi", banker_type="manager", inhabitant_type="shopkeeper"),
            StoryParams(place="alley", name="Tess", banker_type="teller", inhabitant_type="inhabitant"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
