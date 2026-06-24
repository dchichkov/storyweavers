#!/usr/bin/env python3
"""
A small storyworld about a child's performance, with a flashback, a moral turn,
and a little humor, told in a rhyming-story style.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Stage:
    place: str = "the little school stage"
    audience: str = "the children and parents"
    props: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    prop: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mia", "Lina", "Nora", "Zoe", "Ava", "Ivy"]
NAMES_BOY = ["Leo", "Ben", "Max", "Noah", "Sam", "Finn"]
HELPERS = ["friend", "teacher", "sibling"]
PROPS = ["big red hat", "glittery scarf", "toy microphone", "paper crown"]


@dataclass
class World:
    stage: Stage
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return World(stage=copy.deepcopy(self.stage),
                     entities=copy.deepcopy(self.entities),
                     paragraphs=[[]],
                     facts=copy.deepcopy(self.facts),
                     fired=set(self.fired))


def mood_word(m: float) -> str:
    if m >= 2:
        return "very brave"
    if m >= 1:
        return "brave"
    if m <= -1:
        return "nervous"
    return "a little nervous"


def build_world(params: StoryParams) -> World:
    stage = Stage()
    w = World(stage=stage)
    child = w.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"nervous": 0.0, "joy": 0.0, "confidence": 0.0},
        memes={"hope": 0.0, "humor": 0.0, "moral": 0.0},
    ))
    helper = w.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"kindness": 1.0},
        memes={"care": 1.0},
    ))
    prop = w.add(Entity(
        id="prop",
        type="thing",
        label=params.prop,
        owner=child.id,
    ))
    w.facts.update(child=child, helper=helper, prop=prop, params=params)
    return w


def flashback(world: World) -> None:
    c = world.facts["child"]
    h = world.facts["helper"]
    p = world.facts["prop"]
    c.meters["confidence"] += 1
    c.memes["hope"] += 1
    world.say(
        f"Before the bright stage lights began to glow, {c.id} had a tiny flashback in a chair: "
        f"{h.label} had helped {c.id} practice the lines with a laugh and a clap."
    )
    world.say(
        f'"One wrong word can sound funny," {h.label} had said, "but practice makes the story sturdy, like a boat."'
    )
    world.say(
        f"So {c.id} remembered the rhyme and held the {p.label} tight, feeling a bit less shaky."
    )


def start_show(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["prop"]
    world.say(
        f"At {world.stage.place}, {c.id} stepped up for the performance, with {p.label} ready in small hands."
    )
    world.say(
        f"The audience was quiet, and the first line bounced around like a pea in a pot."
    )


def stumble(world: World) -> None:
    c = world.facts["child"]
    c.meters["nervous"] += 1
    c.memes["humor"] += 1
    world.say(
        f"{c.id} squeaked, then giggled, then nearly forgot the next verse."
    )
    world.say(
        f"It was a silly little stumble, the kind that makes a room feel warm, not grumble."
    )


def helper_cheer(world: World) -> None:
    c = world.facts["child"]
    h = world.facts["helper"]
    c.meters["nervous"] -= 1
    c.meters["confidence"] += 1
    c.memes["moral"] += 1
    world.say(
        f"{h.label} gave a wink and a nod, not a fuss or a frown."
    )
    world.say(
        f"That reminded {c.id} that kind help can lift a person right up from the ground."
    )


def finish(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["prop"]
    c.meters["joy"] += 2
    c.meters["confidence"] += 1
    world.say(
        f"Then {c.id} found the rhyme again and sang it out clear."
    )
    world.say(
        f"The crowd clapped along, and the {p.label} bounced like a star in the cheer."
    )
    world.say(
        f"At the end, {c.id} bowed with a grin: after a little help, a brave heart can win."
    )
    world.say(
        f"And the best part of the show was the moral in sight: when friends help each other, the world feels right."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    start_show(world)
    world.para()
    flashback(world)
    stumble(world)
    helper_cheer(world)
    world.para()
    finish(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    p = world.facts["prop"]
    return [
        QAItem(
            question=f"What kind of event was {c.id} taking part in?",
            answer=f"{c.id} was taking part in a performance on a little school stage."
        ),
        QAItem(
            question=f"What did {c.id} remember in the flashback?",
            answer=f"{c.id} remembered practicing the lines with {h.label}, which made the show feel less scary."
        ),
        QAItem(
            question=f"What helped {c.id} finish the show?",
            answer=f"Remembering the practice, getting a kind cheer from {h.label}, and holding the {p.label} helped {c.id} finish."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a performance?",
            answer="A performance is when someone sings, acts, reads, or shows something for other people to watch."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened before."
        ),
        QAItem(
            question="Why can practice help before a show?",
            answer="Practice helps because it makes the words and moves feel familiar, so they are easier to remember."
        ),
        QAItem(
            question="What is a moral?",
            answer="A moral is the lesson a story teaches, like being kind, brave, or helpful."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    h = world.facts["helper"]
    p = world.facts["prop"]
    return [
        f"Write a short rhyming story about {c.id} in a performance with a flashback to practice.",
        f"Tell a gentle story where {h.label} helps {c.id} get through a stage show without losing the rhyme.",
        f"Write a child-friendly story with humor and a moral about helping, using a {p.label}.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    params = CURATED[0]
    return "\n".join([
        asp.fact("event", "performance"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "humor"),
        asp.fact("feature", "moral_value"),
        asp.fact("style", "rhyming_story"),
        asp.fact("requires", "practice"),
        asp.fact("helps", "friend"),
    ])


ASP_RULES = r"""
compatible_story(performance, flashback, humor, moral_value, rhyming_story) :-
    event(performance), feature(flashback), feature(humor), feature(moral_value), style(rhyming_story).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/5."))
    ok = bool(asp.atoms(model, "compatible_story"))
    if ok:
        print("OK: ASP gate recognizes the storyworld features.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming performance storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--prop", choices=PROPS)
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
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    prop = args.prop or rng.choice(PROPS)
    return StoryParams(name=name, gender=gender, helper=helper, prop=prop)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mia", gender="girl", helper="teacher", prop="toy microphone"),
    StoryParams(name="Leo", gender="boy", helper="friend", prop="paper crown"),
    StoryParams(name="Ava", gender="girl", helper="sibling", prop="glittery scarf"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/5."))
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
