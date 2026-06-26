#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pike_transformation_inner_monologue_conflict_slice_of.py
================================================================================================

A small slice-of-life storyworld about a child, a pike, and a quiet choice.

Seed image:
- A child finds a pike near the edge of a pond on an ordinary day.
- The child is unsure whether to keep it in a bucket, show it to someone, or let it go.
- The pike is not a monster; it is simply a living fish that changes once it is returned to the water.
- The story turns on inner monologue, a small conflict, and a gentle transformation.

The world is intentionally compact and constraint-checked:
- Physical state is tracked with meters.
- Emotional state is tracked with memes.
- Prose is driven by simulated state, not a fixed paragraph with swapped nouns.
- The ASP twin mirrors the Python reasonableness gate.
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pond path"
    indoors: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str = "Milo"
    age_word: str = "small"
    parent: str = "dad"
    seed: Optional[int] = None


SETTINGS = {
    "pond": Setting(place="the pond path", indoors=False),
}

NAMES = ["Milo", "Nina", "Rae", "Owen", "Pia", "Luca"]
AGE_WORDS = ["small", "careful", "quiet", "curious", "gentle"]


ASP_RULES = r"""
% A pike is at risk when it is carried away from the pond.
at_risk(pike) :- carried_away(pike).

% The child is conflicted when wanting to keep the fish but also knowing it
% should return to the water.
conflict(child) :- wants_to_keep(child), knows_kind_choice(child).

% A transformation happens when the pike is returned and the stress drops.
transforms(pike) :- at_risk(pike), returned_to_water(pike).

% The story is reasonable only if the fish is actually at risk and can be released.
valid_story(pond, pike, child) :- at_risk(pike), can_release(pike).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "pond"),
        asp.fact("place", "pond", "the_pond_path"),
        asp.fact("character", "child"),
        asp.fact("fish", "pike"),
        asp.fact("can_release", "pike"),
        asp.fact("wants_to_keep", "child"),
        asp.fact("knows_kind_choice", "child"),
        asp.fact("carried_away", "pike"),
        asp.fact("returned_to_water", "pike"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
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
    ap = argparse.ArgumentParser(description="Story world: pike, transformation, inner monologue, conflict.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--age-word", choices=AGE_WORDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [("pond", "pike", "child")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        age_word=args.age_word or rng.choice(AGE_WORDS),
        parent=args.parent or rng.choice(["mom", "dad"]),
        seed=None,
    )


def _do_release(world: World, child: Entity, pike: Entity) -> None:
    if pike.carried_by != child.id:
        return
    pike.carried_by = None
    pike.location = "water"
    pike.meters["stress"] = max(0.0, pike.meters.get("stress", 0.0) - 2.0)
    pike.meters["freedom"] = pike.meters.get("freedom", 0.0) + 2.0
    pike.memes["relief"] = pike.memes.get("relief", 0.0) + 2.0
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    child.memes["confidence"] = child.memes.get("confidence", 0.0) + 1.0
    child.memes["conflict"] = 0.0
    child.memes["tenderness"] = child.memes.get("tenderness", 0.0) + 1.0


def _predict_release(world: World, child: Entity, pike: Entity) -> bool:
    sim = world.copy()
    _do_release(sim, sim.get(child.id), sim.get(pike.id))
    return sim.get(pike.id).location == "water" and sim.get(pike.id).memes.get("relief", 0.0) >= THRESHOLD


def tell(name: str, parent: str, age_word: str) -> World:
    world = World(SETTINGS["pond"])
    child = world.add(Entity(
        id=name,
        kind="character",
        type="child",
        label=name,
        phrase=f"a {age_word} child named {name}",
        memes={"curiosity": 1.0, "worry": 0.0, "conflict": 0.0, "confidence": 0.0},
    ))
    parent_ent = world.add(Entity(
        id=parent,
        kind="character",
        type="parent",
        label=f"their {parent}",
        phrase=f"their {parent}",
    ))
    pike = world.add(Entity(
        id="pike",
        kind="thing",
        type="fish",
        label="pike",
        phrase="a silver pike with a quick tail",
        owner=None,
        carried_by=name,
        location="bucket",
        meters={"stress": 2.0, "freedom": 0.0},
        memes={"fear": 1.0, "relief": 0.0},
    ))

    world.say(
        f"{child.phrase} found a pike near {world.setting.place} one ordinary afternoon. "
        f"{child.pronoun('subject').capitalize()} crouched beside the bucket and watched the fish flick its tail."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} liked the shiny scales, but {child.pronoun('possessive')} thoughts kept tugging in two directions."
    )

    world.para()
    world.say(
        f"Part of {child.pronoun('object')} wanted to keep the pike close and show it to {child.pronoun('possessive')} {parent_ent.id}, "
        f"because it felt like finding a secret treasure."
    )
    world.say(
        f"Another part of {child.pronoun('object')} knew the fish looked cramped and plain unhappy."
    )
    child.memes["conflict"] += 1.0
    child.memes["worry"] += 1.0
    pike.meters["stress"] += 0.5

    world.para()
    world.say(
        f"{parent_ent.pronoun('subject').capitalize()} said they should be careful. "
        f"{child.pronoun('subject').capitalize()} stared at the water and listened to the little argument inside {child.pronoun('possessive')} own head."
    )
    world.say(
        f"'If I keep it here, it will stay pretty,' {child.id} thought. "
        f"'But if I let it go, it might feel better.'"
    )

    if not _predict_release(world, child, pike):
        raise StoryError("This world only tells stories where the pike can safely return to the water.")

    world.para()
    world.say(
        f"At last, {child.id} took a breath and tipped the bucket slowly."
    )
    _do_release(world, child, pike)
    world.say(
        f"The pike slipped back into the pond, and its whole body changed at once: the stiff little stillness left, "
        f"and the fish darted forward as if the water had remembered its name."
    )
    world.say(
        f"{child.id} felt the knot in {child.pronoun('possessive')} chest loosen too. "
        f"{child.pronoun('subject').capitalize()} smiled, because the fish was not a keepsake after all. It was happier alive and free."
    )

    world.facts.update(child=child, parent=parent_ent, pike=pike, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        "Write a short slice-of-life story about a child, a pike, and a hard choice.",
        f"Tell a gentle story where {child.id} hears two thoughts at once about a pike by the pond.",
        "Write a story that includes inner monologue, a small conflict, and a quiet transformation in the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    pike = f["pike"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.phrase} and {child.pronoun('possessive')} {parent.id}, who spend an ordinary day near the pond with a pike.",
        ),
        QAItem(
            question=f"What conflict did {child.id} feel inside?",
            answer=f"{child.id} felt torn between keeping the pike close and letting it go back to the water. One thought wanted a treasure, and the other thought wanted the fish to be safe.",
        ),
        QAItem(
            question=f"What changed when the pike went back into the pond?",
            answer=f"The pike grew calmer and more lively in the water, and {child.id} felt relieved too. That was the story's transformation: the fish returned to where it belonged, and the child became more certain.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pike?",
            answer="A pike is a long, fast freshwater fish with a pointed snout. It swims in lakes, rivers, and ponds and catches smaller fish.",
        ),
        QAItem(
            question="What does a fish need to stay healthy?",
            answer="A fish needs water to breathe and move in. When it goes back into water, it can swim and act naturally again.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in someone's head where they think through a choice before they act.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "character":
            bits.append("kind=character")
        else:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [StoryParams(name="Milo", age_word="quiet", parent="dad")]


def explain_rejection() -> str:
    return "(No story: this world only tells a pike story where the fish can be safely returned to the water.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.parent, params.age_word)
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


def asp_facts_only_program() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_facts_only_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combo(s):")
        for combo in combos:
            print(" ", combo)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
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
