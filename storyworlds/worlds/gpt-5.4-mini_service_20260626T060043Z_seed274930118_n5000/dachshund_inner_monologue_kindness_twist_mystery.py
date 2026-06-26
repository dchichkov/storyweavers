#!/usr/bin/env python3
"""
Standalone storyworld: a dachshund mystery with inner monologue, kindness, and a twist.

Premise:
A small dachshund notices a confusing problem in a quiet neighborhood.
He thinks through clues in his head, helps others kindly, and discovers the
mystery is not what it first seemed.

The story engine keeps a tiny world model with:
- physical meters: distance, carrying, hidden, found, wet, open, etc.
- emotional memes: worry, curiosity, trust, relief, pride, gratitude

It supports:
- a single default story
- random variation from a constrained catalog
- QA generation
- JSON output
- trace output
- ASP parity verification
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str = "the little lane"
    mystery: str = "the missing ribbon"
    clue: str = "a muddy pawprint"
    helper: str = "the baker"
    twist: str = "the ribbon was tied to a kite string"
    name: str = "Pip"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dachshund", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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

        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def mget(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def emget(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def madd(e: Entity, key: str, value: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + value


def eadd(e: Entity, key: str, value: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + value


def has(e: Entity, key: str, at: float = 1.0) -> bool:
    return e.meters.get(key, 0.0) >= at or e.memes.get(key, 0.0) >= at


def narrative_inner_monologue(dog: Entity) -> str:
    if emget(dog, "worry") >= 1:
        return "Pip's thoughts ran in little circles. Something was wrong, and he could almost smell the answer."
    if emget(dog, "curiosity") >= 1:
        return "Pip's mind ticked like a tiny clock. Every clue felt important."
    return "Pip listened to his own thoughts and tried to stay calm."


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name:
        raise StoryError("The dachshund needs a name.")
    if not params.place or not params.mystery or not params.clue or not params.helper:
        raise StoryError("This mystery needs a place, a clue, and a helper.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    w = World()
    dog = w.add(Entity(id="dog", kind="character", type="dachshund", label=params.name))
    helper = w.add(Entity(id="helper", kind="character", type="woman", label=params.helper))
    ribbon = w.add(Entity(id="ribbon", type="thing", label="ribbon", phrase="a bright red ribbon"))
    kite = w.add(Entity(id="kite", type="thing", label="kite", phrase="a paper kite"))
    clue = w.add(Entity(id="clue", type="thing", label="clue", phrase=params.clue, hidden=False))
    w.facts.update(params=params, dog=dog, helper=helper, ribbon=ribbon, kite=kite, clue=clue)

    # Setup
    w.say(f"{params.name} was a small dachshund who loved quiet walks along {params.place}.")
    w.say(f"One afternoon, he noticed {params.mystery}, and that made his ears perk up.")
    eadd(dog, "curiosity", 1)

    # Mystery middle
    w.para()
    w.say(narrative_inner_monologue(dog))
    w.say(f"He sniffed the ground and found {params.clue}.")
    eadd(dog, "worry", 1)
    madd(clue, "found", 1)
    madd(dog, "distance", 1)

    # A kind act that also advances the investigation
    w.say(f"Pip trotted to {params.helper} and nudged the clue forward with his nose.")
    eadd(helper, "gratitude", 1)
    eadd(dog, "kindness", 1)
    eadd(helper, "trust", 1)

    # Twist
    w.para()
    w.say(f"{params.helper} smiled and pointed up.")
    w.say(f"{params.twist.capitalize()}, and the ribbon had drifted down to the lane.")
    madd(ribbon, "found", 1)
    madd(kite, "open", 1)
    eadd(dog, "relief", 1)
    eadd(dog, "pride", 1)

    # Resolution
    w.say(f"Pip wagged hard. The mystery had a surprising answer, and his kind little chase had helped solve it.")
    w.say(f"He took one last proud look at {params.place}, where the ribbon now hung safely in {params.helper}'s hands.")
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a child-friendly mystery about a dachshund named {p.name} on {p.place}.",
        f"Tell a short story with inner monologue, kindness, and a twist involving {p.mystery}.",
        f"Write a gentle mystery where a dachshund finds {p.clue} and discovers a surprising truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    dog = world.facts["dog"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {p.name}, a small dachshund who notices a mystery and thinks carefully about it.",
        ),
        QAItem(
            question=f"What clue did {dog.label} find?",
            answer=f"He found {p.clue}, which helped him follow the mystery.",
        ),
        QAItem(
            question=f"What kind thing did {dog.label} do for {helper.label}?",
            answer=f"He kindly brought the clue to {helper.label} and nudged the search forward.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {p.twist}. That meant the missing ribbon was not stolen at all.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dachshund?",
            answer="A dachshund is a small dog with a long body and short legs.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small bit of information that helps someone solve a problem or mystery.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping or caring about someone in a gentle way.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "lane": "the little lane",
    "garden": "the garden path",
    "square": "the quiet village square",
}

CLUES = [
    "a muddy pawprint",
    "a shiny button",
    "a torn ribbon end",
]

HELPERS = [
    "the baker",
    "the florist",
    "the librarian",
]

TWISTS = [
    "the ribbon was tied to a kite string",
    "the missing ribbon had blown into a tree",
    "the ribbon belonged to a prize kite",
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            for helper in HELPERS:
                for twist in TWISTS:
                    combos.append((place, clue, helper, twist))
    return combos


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    for twist in TWISTS:
        lines.append(asp.fact("twist", twist))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue, Helper, Twist) :- place(Place), clue(Clue), helper(Helper), twist(Twist).
#show valid/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dachshund mystery with kindness and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=[c for c in CLUES])
    ap.add_argument("--helper", choices=[h for h in HELPERS])
    ap.add_argument("--twist", choices=[t for t in TWISTS])
    ap.add_argument("--name")
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
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if args.twist:
        combos = [c for c in combos if c[3] == args.twist]
    if not combos:
        raise StoryError("No valid mystery setup matches those options.")
    place, clue, helper, twist = rng.choice(combos)
    return StoryParams(
        place=SETTINGS[place],
        mystery="the missing ribbon",
        clue=clue,
        helper=helper,
        twist=twist,
        name=args.name or rng.choice(["Pip", "Milo", "Bean", "Toby", "Scout"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place=SETTINGS["lane"], clue="a muddy pawprint", helper="the baker", twist="the ribbon was tied to a kite string", name="Pip"),
    StoryParams(place=SETTINGS["garden"], clue="a torn ribbon end", helper="the florist", twist="the ribbon had blown into a tree", name="Milo"),
    StoryParams(place=SETTINGS["square"], clue="a shiny button", helper="the librarian", twist="the ribbon belonged to a prize kite", name="Bean"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid mystery combos:\n")
        for c in combos[:50]:
            print(" ", c)
        if len(combos) > 50:
            print(f"... and {len(combos) - 50} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
