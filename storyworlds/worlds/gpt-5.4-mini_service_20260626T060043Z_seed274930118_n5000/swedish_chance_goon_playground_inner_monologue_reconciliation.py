#!/usr/bin/env python3
"""
A standalone storyworld for a heartwarming playground tale about a chance
meeting, a scary-looking goon, an inner monologue, and reconciliation.

The seed image:
- A child is playing at a playground on a lucky afternoon.
- A strange goon shows up and seems unfriendly.
- The child thinks privately, decides to be kind, and discovers the goon is
  actually lonely and gentle.
- They reconcile over a small Swedish treat and end the story together.

This world models:
- physical meters: distance, hunger, tiredness, snack
- emotional memes: fear, curiosity, shame, hope, kindness, lonely, trust, joy

It keeps the story child-facing, concrete, and state-driven.
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
    plural: bool = False
    owner: Optional[str] = None
    with_whom: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
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
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mia", "Lina", "Nora", "Ava", "Sofia"],
    "boy": ["Leo", "Oskar", "Nils", "Eli", "Milo"],
}
PARENTS = {"mother": "mom", "father": "dad"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming playground storyworld.")
    ap.add_argument("--name", choices=sorted(set(NAMES["girl"] + NAMES["boy"])))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent)


def clamp(v: float) -> float:
    return 0.0 if abs(v) < 1e-9 else v


def build_world(params: StoryParams) -> World:
    w = World(setting="playground")
    child = w.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"distance": 0.0, "snack": 0.0},
        memes={"curiosity": 0.0, "fear": 0.0, "hope": 0.0, "kindness": 0.0, "joy": 0.0},
    ))
    parent = w.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=PARENTS[params.parent],
        meters={"distance": 0.0},
        memes={"calm": 0.0, "trust": 0.0},
    ))
    goon = w.add(Entity(
        id="goon",
        kind="character",
        type="goon",
        label="the goon",
        meters={"distance": 4.0, "hunger": 1.0, "tiredness": 1.0},
        memes={"scary": 1.0, "lonely": 1.0, "shame": 0.0, "trust": 0.0, "joy": 0.0},
    ))
    treat = w.add(Entity(
        id="treat",
        kind="thing",
        type="snack",
        label="Swedish cinnamon bun",
        phrase="a warm Swedish cinnamon bun",
        owner="child",
        plural=False,
        meters={"sweetness": 1.0},
    ))

    # Act 1: playground and chance encounter.
    w.say(
        f"At the playground, {params.name} was climbing the little blue ladder when "
        f"a stranger stepped through the gate by chance."
    )
    w.say(
        f"The stranger looked big and gruff, so everyone called him the goon."
    )
    child.memes["curiosity"] += 1.0
    child.memes["fear"] += 1.0
    parent.memes["calm"] += 1.0
    w.say(
        f"{params.name} held still and watched. {child.pronoun().capitalize()} felt a tiny wobble in {child.pronoun('possessive')} chest."
    )

    # Act 2: inner monologue.
    w.para()
    w.say(
        f"In {child.pronoun('possessive')} inner monologue, {params.name} thought, "
        f'"He looks like a goon, but maybe he is just sad or lost."'
    )
    child.memes["hope"] += 1.0
    child.memes["kindness"] += 1.0

    # Act 3: reconciliation path.
    w.say(
        f"{params.name} walked a few careful steps closer and offered {child.pronoun('possessive')} warm Swedish cinnamon bun."
    )
    child.meters["snack"] -= 1.0
    goon.meters["hunger"] -= 1.0
    goon.memes["shame"] += 1.0
    goon.memes["trust"] += 1.0
    w.say(
        f"The goon blinked, then took the bun with both hands. He admitted he had come to the playground because he felt lonely."
    )
    goon.memes["lonely"] = 0.0
    goon.memes["scary"] = 0.0
    goon.memes["joy"] += 1.0
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1.0
    parent.memes["trust"] += 1.0

    w.para()
    w.say(
        f"That was the moment of reconciliation: {params.name} smiled, the goon smiled back, and the big stranger did not seem big anymore."
    )
    w.say(
        f"Soon they were taking turns on the swing, and the playground sounded softer than before."
    )
    w.say(
        f"By the end, {params.name} had a new friend, and the goon had a warm place in the day."
    )

    w.facts.update(
        child=child,
        parent=parent,
        goon=goon,
        treat=treat,
        params=params,
        place="playground",
        incident="chance encounter",
    )
    return w


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    child = world.facts["child"]
    return [
        'Write a heartwarming story set in a playground about a chance meeting with a goon, including an inner monologue and reconciliation.',
        f"Tell a gentle story where {child.label} meets a scary-looking goon at the playground, thinks privately, and chooses kindness.",
        f'Write a short child-friendly story that uses the words "swedish", "chance", and "goon" and ends with friends on the swings.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    goon = world.facts["goon"]
    params = world.facts["params"]
    return [
        QAItem(
            question="Where does the story take place?",
            answer="It takes place at the playground.",
        ),
        QAItem(
            question=f"What did {params.name} think during the inner monologue?",
            answer=(
                f"{params.name} thought the goon looked scary, but maybe he was just sad or lost. "
                f"That thought helped {child.pronoun('object')} choose kindness."
            ),
        ),
        QAItem(
            question="What made the goon stop seeming scary?",
            answer=(
                "He accepted the Swedish cinnamon bun, admitted he was lonely, and smiled back. "
                "After that, he felt like a friend instead of a stranger."
            ),
        ),
        QAItem(
            question=f"How did {params.name} and the goon end the story?",
            answer=(
                f"They reconciled, smiled at each other, and took turns on the swing together. "
                f"{params.name} ended with a new friend."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a playground for?",
            answer="A playground is a place where children can climb, swing, slide, and play with others.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after worry, misunderstanding, or hurt feelings.",
        ),
        QAItem(
            question="What is a Swedish cinnamon bun?",
            answer="A Swedish cinnamon bun is a sweet baked treat with cinnamon, often warm and soft.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: clamp(v) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: clamp(v) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:6} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Playground world ASP twin.
entity(child).
entity(parent).
entity(goon).
place(playground).

chance_meeting(child, goon) :- place(playground), entity(child), entity(goon).
inner_monologue(child) :- chance_meeting(child, goon), fear(child), curiosity(child).
reconcile(child, goon) :- inner_monologue(child), offers(child, swedish_bun), lonely(goon).

#show chance_meeting/2.
#show inner_monologue/1.
#show reconcile/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("entity", "child"),
            asp.fact("entity", "parent"),
            asp.fact("entity", "goon"),
            asp.fact("place", "playground"),
            asp.fact("fear", "child"),
            asp.fact("curiosity", "child"),
            asp.fact("offers", "child", "swedish_bun"),
            asp.fact("lonely", "goon"),
        ]
    )


def asp_program(show: str) -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show chance_meeting/2. #show inner_monologue/1. #show reconcile/2."))
    atoms = {str(a) for a in model}
    expected = {"chance_meeting(child,goon)", "inner_monologue(child)", "reconcile(child,goon)"}
    if atoms == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show chance_meeting/2.\n#show inner_monologue/1.\n#show reconcile/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
        except Exception as e:
            print(f"ASP unavailable: {e}")
            sys.exit(1)
        model = asp.one_model(asp_program("#show chance_meeting/2.\n#show inner_monologue/1.\n#show reconcile/2."))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = [
            StoryParams(name="Mia", gender="girl", parent="mother"),
            StoryParams(name="Leo", gender="boy", parent="father"),
            StoryParams(name="Nora", gender="girl", parent="father"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            p = resolve_params(args, rng)
            p.seed = seed
            sample = generate(p)
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
