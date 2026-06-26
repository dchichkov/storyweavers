#!/usr/bin/env python3
"""
A small rhyming story world about an ambiguous drawing, a confidante, and a
twist that makes the ending shine.

The seed tale premise:
A child starts a drawing from a puzzling clue. A trusted confidante helps the
child think through the ambiguity. The linework turns into a surprising picture,
and the twist lands when the drawing is finally revealed.

This script builds that premise as a tiny simulation with physical meters and
emotional memes, plus a matching ASP twin for verification.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_m(self, key: str, delta: float) -> None:
        self.meters[key] = self.m(key) + delta

    def add_e(self, key: str, delta: float) -> None:
        self.memes[key] = self.e(key) + delta

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the art nook"
    affords: set[str] = field(default_factory=set)


@dataclass
class Prompt:
    clue: str
    topic: str
    twist: str
    answer: str
    risk: str


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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PROMPTS = [
    Prompt(
        clue="a moon with a hidden grin",
        topic="moon",
        twist="the moon is actually a smiling cat",
        answer="a moon-cat",
        risk="The clue could stay too vague and leave the page blank."
    ),
    Prompt(
        clue="a tiny house inside a tree",
        topic="tree",
        twist="the house is a bird nest in disguise",
        answer="a nest-house",
        risk="The clue could be misread as a real house instead of a nest."
    ),
    Prompt(
        clue="a ship that sleeps in a pond",
        topic="ship",
        twist="the ship is a toy boat with a blanket",
        answer="a toy boat",
        risk="The clue could point to the wrong kind of ship."
    ),
    Prompt(
        clue="a dragon made of lines and light",
        topic="dragon",
        twist="the dragon is a kite caught in sunset glow",
        answer="a kite-dragon",
        risk="The clue could seem scary until the shape is seen clearly."
    ),
]


GENTLE_NAMES = ["Mina", "Noah", "Luna", "Theo", "Iris", "Niko", "Pia", "Sam"]
TRAITS = ["curious", "brave", "gentle", "bright", "dreamy", "spry"]


@dataclass
class StoryParams:
    place: str
    clue: str
    topic: str
    twist: str
    answer: str
    name: str
    trait: str
    seed: Optional[int] = None


SETTING = Setting(place="the art nook", affords={"draw"})
VALID_TOPICS = {p.topic for p in PROMPTS}


ASP_RULES = r"""
% A prompt is valid if the child can draw from a clue, the clue is ambiguous,
% and a confidante can help resolve the twist.
valid_prompt(C) :- clue(C), ambiguous(C), drawable(C), has_confidante(C).

% The final twist is acceptable when the drawing can be read in two ways first,
% then resolved by the reveal.
twist_ok(C) :- valid_prompt(C), has_twist(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "art_nook"))
    lines.append(asp.fact("affords", "art_nook", "draw"))
    for p in PROMPTS:
        pid = p.topic
        lines.append(asp.fact("clue", pid))
        lines.append(asp.fact("ambiguous", pid))
        lines.append(asp.fact("drawable", pid))
        lines.append(asp.fact("has_confidante", pid))
        lines.append(asp.fact("has_twist", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_prompts() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_prompt/1."))
    return sorted(set(a[0] for a in asp.atoms(model, "valid_prompt")))


def asp_verify() -> int:
    py = {p.topic for p in PROMPTS}
    cl = set(asp_valid_prompts())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} prompts).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world with an ambiguous drawing and a twist.")
    ap.add_argument("--place", choices=["art nook"], default="art nook")
    ap.add_argument("--topic", choices=sorted(VALID_TOPICS))
    ap.add_argument("--name")
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
    choices = PROMPTS
    if args.topic:
        choices = [p for p in choices if p.topic == args.topic]
    if not choices:
        raise StoryError("(No valid prompt matches the given options.)")
    p = rng.choice(choices)
    name = args.name or rng.choice(GENTLE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="art nook",
        clue=p.clue,
        topic=p.topic,
        twist=p.twist,
        answer=p.answer,
        name=name,
        trait=trait,
    )


def intro_lines(world: World, child: Entity, confidante: Entity, prompt: Prompt) -> None:
    world.say(
        f"{child.id} was a {child.trait_word} little {child.type} who loved to draw with a steady glow."
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        owner=None,
        caretaker=None,
        meters={"ink": 0.0, "draw": 0.0, "reveal": 0.0},
        memes={"worry": 0.0, "trust": 0.0, "joy": 0.0, "wonder": 0.0, "surprise": 0.0},
    ))
    child.trait_word = params.trait  # type: ignore[attr-defined]
    confidante = world.add(Entity(
        id="Confidante",
        kind="character",
        type="friend",
        label="a confidante",
        meters={"ink": 0.0},
        memes={"trust": 0.0, "joy": 0.0},
    ))
    paper = world.add(Entity(
        id="Paper",
        type="paper",
        label="paper",
        phrase="blank paper",
        meters={"blank": 1.0, "ink": 0.0, "shape": 0.0, "shine": 0.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        type="clue",
        label="clue",
        phrase=params.clue,
        meters={"ambiguous": 1.0},
        memes={"mystery": 1.0},
    ))
    twist = world.add(Entity(
        id="Twist",
        type="twist",
        label="twist",
        phrase=params.twist,
        meters={"reveal": 0.0},
        memes={"surprise": 1.0},
    ))

    world.facts.update(child=child, confidante=confidante, paper=paper, clue=clue, twist=twist, params=params)

    world.say(
        f"At {world.setting.place}, {child.id} stared at {params.clue} and gave a little thinky twist."
    )
    world.say(
        f"The clue was ambiguous, so the lines looked shy, and the first draw was not yet in sight."
    )
    world.para()
    child.add_e("worry", 1.0)
    world.say(
        f"{child.id} wanted a picture that would sing, but the puzzle was slippery and not quite right."
    )
    confidante.add_e("trust", 1.0)
    child.add_e("trust", 1.0)
    world.say(
        f"Then the confidante leaned near and grinned, 'Try the clue one way, then try it another tonight.'"
    )
    world.say(
        f"{child.id} drew a rounder line, then a longer line, and the page began to glow in the light."
    )
    child.add_m("draw", 1.0)
    paper.add_m("ink", 1.0)
    paper.add_m("shape", 1.0)
    child.add_e("joy", 1.0)
    child.add_e("wonder", 1.0)
    world.para()
    world.say(
        f"The twist came quick: the {params.answer} was hiding inside the clue, and the answer felt right."
    )
    paper.add_m("reveal", 1.0)
    twist.add_m("reveal", 1.0)
    child.add_e("surprise", 1.0)
    confidante.add_e("joy", 1.0)
    world.say(
        f"{child.id} laughed, the confidante clapped, and the once-ambiguous draw turned bright."
    )
    world.say(
        f"So the page held the {params.answer}, a little surprise, and a happy, rhyming sight."
    )
    return world


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
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short rhyming story for a child named {p.name} who tries to draw {p.clue} and needs a confidante.",
        f"Tell a gentle story where an ambiguous draw leads to a twist and the answer becomes {p.answer}.",
        f"Create a tiny story with the words confidante, ambiguous, draw, and Twist, ending in a happy reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    qa = [
        QAItem(
            question=f"What did {child.id} try to do at the art nook?",
            answer=f"{child.id} tried to draw a picture from a clue that was a little ambiguous."
        ),
        QAItem(
            question=f"Who helped {child.id} when the clue felt hard to read?",
            answer="A confidante helped by encouraging the child to try the clue in two different ways."
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {p.answer} was hiding inside {p.twist}."
        ),
    ]
    if world.facts["child"].e("surprise") >= THRESHOLD:
        qa.append(
            QAItem(
                question="How did the child feel at the end?",
                answer="The child felt happy and surprised, because the tricky clue turned into a bright reveal."
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ambiguous mean?",
            answer="Ambiguous means something can be understood in more than one way."
        ),
        QAItem(
            question="What is a confidante?",
            answer="A confidante is a trusted friend someone can share worries with."
        ),
        QAItem(
            question="What does it mean to draw?",
            answer="To draw is to make a picture with lines, shapes, and marks on paper."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how the ending feels."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs an ambiguous clue, a confidante, and a twist that can still resolve into a draw.)"


def asp_facts_only() -> str:
    return asp_facts()


def asp_valid_topics() -> list[str]:
    return [p.topic for p in PROMPTS]


def asp_verify_program() -> int:
    py = set(asp_valid_topics())
    cl = set(asp_valid_prompts())
    if py == cl:
        print(f"OK: clingo gate matches valid prompt set ({len(py)} topics).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_sample_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_prompt/1."))
        return
    if args.verify:
        sys.exit(asp_verify_program())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_prompt/1."))
        vals = sorted(set(asp.atoms(model, "valid_prompt")))
        print(f"{len(vals)} valid prompts:")
        for v in vals:
            print(" ", v[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(
                place="art nook",
                clue=p.clue,
                topic=p.topic,
                twist=p.twist,
                answer=p.answer,
                name=GENTLE_NAMES[i % len(GENTLE_NAMES)],
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            for i, p in enumerate(PROMPTS)
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            print(f"### {sample.params.name}: {sample.params.topic}")
        elif len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
