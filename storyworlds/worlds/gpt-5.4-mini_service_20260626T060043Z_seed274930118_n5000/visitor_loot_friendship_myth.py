#!/usr/bin/env python3
"""
storyworlds/worlds/visitor_loot_friendship_myth.py
===================================================

A small myth-style story world about a visitor, a treasured loot item, and a
friendship that changes what the treasure means.

Premise:
A visitor arrives at an old sacred place carrying loot found on the road. The
local keeper sees the loot as a possible offering, not a prize to hoard. The
visitor and keeper test each other, then choose friendship over greed, and the
story ends with the loot given a new purpose.

The simulated world keeps track of:
- physical meters: carried weight, distance, wear, shelter, offering
- emotional memes: trust, suspicion, gratitude, pride, friendship

The prose is generated from that state, not from a fixed paragraph template.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    gifted_to: Optional[str] = None
    sacred: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"weight": 0.0, "distance": 0.0, "offered": 0.0, "kept": 0.0}
        if not self.memes:
            self.memes = {
                "trust": 0.0,
                "suspicion": 0.0,
                "gratitude": 0.0,
                "pride": 0.0,
                "friendship": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "keeper", "priestess"}
        male = {"boy", "man", "father", "visitor", "priest", "guardian"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mode: str  # "shore" | "grove" | "cave" | "ruins"
    affords: set[str] = field(default_factory=set)


@dataclass
class Loot:
    id: str
    label: str
    phrase: str
    kind: str
    weight: float
    sacred_fit: bool
    giftable: bool = True
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    loot: str
    visitor_name: str
    visitor_type: str
    keeper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "shore": Setting(place="the moonlit shore", mode="shore", affords={"shell", "coin"}),
    "grove": Setting(place="the elder grove", mode="grove", affords={"seed", "torch"}),
    "cave": Setting(place="the echo cave", mode="cave", affords={"gem", "torch"}),
    "ruins": Setting(place="the quiet ruins", mode="ruins", affords={"coin", "gem"}),
}

LOOTS = {
    "shell": Loot(id="shell", label="shell", phrase="a pearl-white shell", kind="shell", weight=1.0, sacred_fit=True),
    "coin": Loot(id="coin", label="coin", phrase="an old bronze coin", kind="coin", weight=1.0, sacred_fit=True),
    "seed": Loot(id="seed", label="seed", phrase="a bright seed in a clay bead", kind="seed", weight=1.0, sacred_fit=True),
    "torch": Loot(id="torch", label="torch", phrase="a small torch wrapped in resin cloth", kind="torch", weight=2.0, sacred_fit=False),
    "gem": Loot(id="gem", label="gem", phrase="a deep blue gem", kind="gem", weight=1.0, sacred_fit=True),
}

VISITOR_NAMES = ["Ari", "Mina", "Tavi", "Lena", "Rin", "Sora", "Noa", "Ivo"]
TRAITS = ["restless", "gentle", "brave", "curious", "quiet", "hopeful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for loot_id in setting.affords:
            loot = LOOTS[loot_id]
            if loot.sacred_fit:
                combos.append((place, loot_id))
    return combos


def prize_at_risk(setting: Setting, loot: Loot) -> bool:
    return loot.id in setting.affords and loot.sacred_fit


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("mode", sid, s.mode))
        for loot_id in sorted(s.affords):
            lines.append(asp.fact("affords", sid, loot_id))
    for lid, l in LOOTS.items():
        lines.append(asp.fact("loot", lid))
        if l.sacred_fit:
            lines.append(asp.fact("sacred_fit", lid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Loot) :- affords(Place, Loot), sacred_fit(Loot).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: a visitor, a loot, and a friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--loot", choices=LOOTS)
    ap.add_argument("--name")
    ap.add_argument("--visitor-type", choices=["visitor", "boy", "girl"])
    ap.add_argument("--keeper-type", choices=["keeper", "guardian", "woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.loot is None or c[1] == args.loot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, loot = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        loot=loot,
        visitor_name=args.name or rng.choice(VISITOR_NAMES),
        visitor_type=args.visitor_type or "visitor",
        keeper_type=args.keeper_type or rng.choice(["keeper", "guardian"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def _do_arrival(world: World, visitor: Entity, keeper: Entity, loot: Entity) -> None:
    visitor.meters["distance"] += 1
    loot.carried_by = visitor.id
    loot.meters["weight"] = LOOTS[loot.type].weight
    visitor.memes["pride"] += 1
    visitor.memes["trust"] += 1
    world.say(
        f"One evening, {visitor.id}, a {visitor.memes['pride'] and world.facts['trait']} {visitor.type}, "
        f"came to {world.setting.place} carrying {loot.phrase}."
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    visitor = world.add(Entity(id=params.visitor_name, kind="character", type=params.visitor_type))
    keeper = world.add(Entity(id="keeper", kind="character", type=params.keeper_type))
    loot = world.add(Entity(
        id="loot",
        kind="thing",
        type=params.loot,
        label=LOOTS[params.loot].label,
        phrase=LOOTS[params.loot].phrase,
        caretaker=keeper.id,
    ))
    world.facts.update(visitor=visitor, keeper=keeper, loot=loot, trait=params.trait, place=params.place)

    visitor.memes["pride"] += 1
    visitor.memes["trust"] += 1
    loot.meters["weight"] = LOOTS[params.loot].weight

    world.say(
        f"{visitor.id} was a {params.trait} {visitor.type} who had crossed far roads."
    )
    world.say(
        f"{visitor.pronoun().capitalize()} came to {world.setting.place} with {loot.phrase} tucked close."
    )
    world.say(
        f"At the gate stood a {keeper.type}, watching the {loot.label} with careful eyes."
    )

    world.para()
    visitor.memes["suspicion"] += 0.0
    keeper.memes["suspicion"] += 1.0
    world.say(
        f"The {keeper.type} said, \"Many hands can hold a treasure, but not every hand should keep it.\""
    )
    visitor.memes["pride"] += 1
    world.say(
        f"{visitor.id} clutched {loot.it()} tighter, for {visitor.pronoun('possessive')} heart still loved the shine of it."
    )

    world.para()
    if LOOTS[params.loot].sacred_fit:
        keeper.memes["trust"] += 1
        world.say(
            f"Then the {keeper.type} told an older truth: that some loot is strongest when it is shared."
        )
        world.say(
            f"{visitor.id} listened, and the hard feeling in {visitor.pronoun('possessive')} chest began to soften."
        )
        visitor.memes["suspicion"] += 0.0
        visitor.memes["friendship"] += 1
        keeper.memes["friendship"] += 1
        visitor.memes["gratitude"] += 1
        loot.meters["offered"] += 1
        loot.carried_by = None
        loot.gifted_to = keeper.id
        world.say(
            f"{visitor.id} laid {loot.it()} on the stone altar and said, \"Let us be friends over this.\""
        )
        world.say(
            f"The {keeper.type} smiled, and the two of them guarded the {loot.label} together."
        )
        world.say(
            f"By dawn, {loot.phrase} was no longer only a prize; it had become a pledge between them."
        )
    else:
        raise StoryError("(This loot does not support the mythic friendship turn.)")

    world.facts.update(resolved=True)
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
    visitor = f["visitor"]
    loot = f["loot"]
    return [
        f'Write a short myth about a visitor who arrives with a {loot.label} and learns the value of friendship.',
        f"Tell a gentle legend where {visitor.id} carries {loot.phrase} to {world.setting.place} and meets a keeper.",
        f'Write a simple mythic story that includes the words "visitor" and "loot" and ends with two strangers becoming friends.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    visitor = f["visitor"]
    keeper = f["keeper"]
    loot = f["loot"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who came to {world.setting.place} with the {loot.label}?",
            answer=f"{visitor.id} came to {world.setting.place} with {loot.phrase}. {visitor.pronoun().capitalize()} was a {trait} {visitor.type}.",
        ),
        QAItem(
            question=f"Why did the {keeper.type} watch the {loot.label} so carefully?",
            answer=f"The {keeper.type} watched carefully because the {loot.label} looked like sacred loot, and not every treasure should be kept alone.",
        ),
        QAItem(
            question=f"What changed when {visitor.id} placed the {loot.label} on the altar?",
            answer=f"The mood changed from caution to friendship. The {loot.label} became a shared pledge, and both of them gained trust and gratitude.",
        ),
        QAItem(
            question=f"How did the story end for {visitor.id} and the {keeper.type}?",
            answer=f"They became friends and guarded the loot together. The ending image is the {loot.label} resting on the altar while both of them kept watch.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    loot = world.facts["loot"]
    return [
        QAItem(question="What is a visitor?", answer="A visitor is someone who comes to a place and is not from there."),
        QAItem(question="What is loot?", answer="Loot is treasure or goods taken or found during a journey, though in stories it can also mean a found treasure that matters a lot."),
        QAItem(question="What is friendship?", answer="Friendship is the feeling and bond that grows when people care for each other and choose to help each other."),
        QAItem(question=f"Why might a {loot.label} be important in a myth?", answer=f"In a myth, a {loot.label} can stand for a promise, a gift, or a memory that people choose to honor together."),
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.gifted_to:
            bits.append(f"gifted_to={e.gifted_to}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shore", loot="shell", visitor_name="Ari", visitor_type="visitor", keeper_type="guardian", trait="curious"),
    StoryParams(place="grove", loot="seed", visitor_name="Mina", visitor_type="girl", keeper_type="keeper", trait="gentle"),
    StoryParams(place="ruins", loot="coin", visitor_name="Tavi", visitor_type="boy", keeper_type="guardian", trait="hopeful"),
    StoryParams(place="cave", loot="gem", visitor_name="Lena", visitor_type="visitor", keeper_type="keeper", trait="brave"),
]


def resolve_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.loot is None or c[1] == args.loot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, loot = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        loot=loot,
        visitor_name=args.name or rng.choice(VISITOR_NAMES),
        visitor_type=args.visitor_type or "visitor",
        keeper_type=args.keeper_type or rng.choice(["keeper", "guardian"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    loot = world.facts["loot"]
    return [
        QAItem(question="What is a visitor?", answer="A visitor is someone who comes to a place and is not from there."),
        QAItem(question="What is loot?", answer="Loot is treasure or goods taken or found during a journey."),
        QAItem(question="What is friendship?", answer="Friendship is the bond that grows when people choose to care for each other."),
        QAItem(question=f"Why might a {loot.label} matter in a story?", answer=f"A {loot.label} can matter because it can become a gift, a promise, or a shared treasure."),
    ]


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
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible (place, loot) combos:\n")
        for place, loot in vals:
            print(f"  {place:12} {loot}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_choices(args, random.Random(seed))
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
            header = f"### {p.visitor_name}: {p.loot} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
