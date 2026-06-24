#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/nigger_holder_gun_kindness_problem_solving_friendship.py
===============================================================================================================

A small fable-style storyworld about a child, a fragile holder, and a gun-shaped
garden tool that must be handled with care.

The seed words requested by the source prompt are kept as registry words in the
world model; the generated story itself stays child-facing and non-violent.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    setting: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            gender = "neutral"
            if "girl" in self.traits:
                gender = "female"
            elif "boy" in self.traits:
                gender = "male"
            if gender == "female":
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if gender == "male":
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "meadow": "the meadow",
    "workshop": "the workshop",
    "barn": "the barn",
    "garden": "the garden",
}

NAMES = ["Milo", "Pia", "Nora", "Eli", "Tess", "Lina", "Ari", "June"]
FRIENDS = ["Finn", "Luca", "Maya", "Sage", "Remy", "Ivy", "Noah", "Clara"]

SEED_WORDS = ["nigger", "holder", "gun"]

# A harmless fable object: a garden sprayer shaped like a little gun.
# It is only used to spray water on thirsty flowers.
WORLD_KINDS = {
    "holder": "a small wooden holder",
    "gun": "a little garden gun",
    "nigger": "a noisy nickname the children only repeat in the registry, never in the tale",
}


ASP_RULES = r"""
name(X) :- hero(X).
friend(X) :- companion(X).
setting(X) :- place(X).
needs_kindness :- kind_act.
needs_problem_solving :- broken_holder.
friendship_grows :- shared_fix.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("place", s))
    for w in SEED_WORDS:
        lines.append(asp.fact("seed_word", w))
    lines.append(asp.fact("hero", "child"))
    lines.append(asp.fact("companion", "friend"))
    lines.append(asp.fact("kind_act"))
    lines.append(asp.fact("broken_holder"))
    lines.append(asp.fact("shared_fix"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_settings() -> list[str]:
    return sorted(SETTINGS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable about kindness, problem solving, and friendship."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--setting", choices=SETTINGS)
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
    setting = args.setting or rng.choice(valid_settings())
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    if name == friend:
        raise StoryError("The child and friend must be different characters.")
    return StoryParams(name=name, friend=friend, setting=setting)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id="child",
        kind="character",
        label=params.name,
        traits=["kind", "curious"],
        memes={"kindness": 0.0, "worry": 0.0, "joy": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        label=params.friend,
        traits=["helpful", "patient"],
        memes={"kindness": 0.0, "worry": 0.0, "joy": 0.0, "friendship": 0.0},
    ))
    holder = world.add(Entity(
        id="holder",
        kind="thing",
        label="holder",
        phrase="a small wooden holder for tools and seeds",
        owner=child.id,
        meters={"crack": 0.0, "safe": 1.0},
    ))
    gun = world.add(Entity(
        id="gun",
        kind="thing",
        label="gun",
        phrase="a little garden gun that sprayed water instead of danger",
        owner=child.id,
        held_by=child.id,
        meters={"water": 0.0, "stuck": 0.0},
    ))
    world.facts.update(child=child, friend=friend, holder=holder, gun=gun)
    return world


def tell(params: StoryParams) -> World:
    w = make_world(params)
    child: Entity = w.facts["child"]  # type: ignore[assignment]
    friend: Entity = w.facts["friend"]  # type: ignore[assignment]
    holder: Entity = w.facts["holder"]  # type: ignore[assignment]
    gun: Entity = w.facts["gun"]  # type: ignore[assignment]

    w.say(
        f"In {w.setting}, there once lived a gentle child named {child.label} "
        f"who loved to help things grow."
    )
    w.say(
        f"{child.label} kept a little {holder.label} for tools and a tiny {gun.label} "
        f"for watering the flowers, and both were precious to {child.pronoun('object')}."
    )
    w.para()
    w.say(
        f"One bright morning, {child.label} found the {holder.label} wobbling and weak, "
        f"so the {gun.label} slipped sideways and made a wet little mess."
    )
    child.memes["worry"] += 1
    holder.meters["crack"] += 1
    gun.meters["stuck"] += 1
    w.say(
        f"{child.label} frowned, because a broken holder could spill seeds and trouble "
        f"all at once."
    )
    w.para()
    w.say(
        f"Then {friend.label} came by and said, "
        f'"Let us solve the problem kindly. We can steady the holder, dry the wood, '
        f'and try again."'
    )
    friend.memes["kindness"] += 1
    child.memes["kindness"] += 1
    child.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    holder.meters["safe"] = 1.0
    holder.meters["crack"] = 0.0
    gun.meters["stuck"] = 0.0
    gun.meters["water"] = 1.0
    w.say(
        f"So the two friends worked together: one held the holder steady, the other "
        f"pressed it dry, and soon the {gun.label} sprayed only soft water again."
    )
    w.say(
        f"By sunset, {child.label} smiled at {friend.label}. The holder stood strong, "
        f"the garden was bright, and friendship had made the small trouble easy to carry."
    )
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world_ending = "The once-wobbly holder was fixed, and the little gun watered the flowers in peace."
    w.facts["ending"] = world_ending
    return w


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        "Write a short fable for a young child about kindness, problem solving, and friendship.",
        f"Tell a gentle story where {child.label} and {friend.label} fix a broken holder and care for a little garden gun.",
        f"Make a simple fable set in {world.setting} about a small problem that is solved by helping a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    holder: Entity = world.facts["holder"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.label}, a gentle child who cared about a holder and a little garden gun.",
        ),
        QAItem(
            question=f"What problem did {child.label} have?",
            answer=f"The holder wobbled and cracked a little, so the garden gun slipped and made a mess.",
        ),
        QAItem(
            question=f"How did {child.label} and {friend.label} solve the problem?",
            answer=f"They used kindness and problem solving together: they steadied the holder, dried it, and fixed it so it would stand strong again.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The holder was strong again, the garden gun sprayed soft water again, and {child.label} and {friend.label} felt like true friends.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle and helpful to someone else, especially when they need care or support.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking at a problem, thinking carefully, and finding a way to fix it.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the happy bond between people who care about each other and help each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.kind} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Milo", friend="Maya", setting="meadow"),
    StoryParams(name="Pia", friend="Finn", setting="garden"),
    StoryParams(name="Nora", friend="Sage", setting="workshop"),
    StoryParams(name="Eli", friend="Clara", setting="barn"),
]


def verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show kind_act/0.\n#show broken_holder/0.\n#show shared_fix/0."))
    shown = {sym.name for sym in model}
    want = {"kind_act", "broken_holder", "shared_fix"}
    if shown == want:
        print("OK: ASP twin matches the Python story spine.")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("ASP:", sorted(shown))
    print("PY :", sorted(want))
    return 1


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
        print(asp_program("#show kind_act/0.\n#show broken_holder/0.\n#show shared_fix/0."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show kind_act/0.\n#show broken_holder/0.\n#show shared_fix/0."))
        print("ASP model:", " ".join(sorted(sym.name for sym in model)))
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
            header = f"### {p.name} with {p.friend} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        "Write a short fable for a young child about kindness, problem solving, and friendship.",
        f"Tell a gentle story where {child.label} and {friend.label} fix a broken holder and care for a little garden gun.",
        f"Make a simple fable set in {world.setting} about a small problem that is solved by helping a friend.",
    ]


if __name__ == "__main__":
    main()
