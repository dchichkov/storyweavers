#!/usr/bin/env python3
"""
A small bedtime-story world set at a marina.

A little child helps at the marina, where a yoke can carry two things at once.
The story has a gentle problem, a talking helper, and a rhyming fix that makes
the night feel safe and cozy again.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"wet": 0.0, "tired": 0.0, "safe": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0, "worry": 0.0, "joy": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str = "marina"
    name: str = "Mina"
    gender: str = "girl"
    helper: str = "mother"
    object: str = "yoke"
    seed: Optional[int] = None


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool = False


SETTINGS = {
    "marina": "a quiet marina with sleepy boats and small wooden docks",
}

HERO_NAMES = ["Mina", "Nora", "Lily", "Iris", "Tia", "Ruby"]
HELPERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["gentle", "curious", "brave", "sleepy", "careful"]

OBJECTS = {
    "yoke": Item(
        id="yoke",
        label="yoke",
        phrase="a small wooden yoke",
        kind="tool",
        risky=True,
    ),
}

WORLD_KNOWLEDGE = {
    "yoke": [
        QAItem(
            question="What is a yoke?",
            answer="A yoke is a bar or frame that helps carry or hold more than one thing at once.",
        ),
        QAItem(
            question="Why can a yoke help with carrying?",
            answer="A yoke helps balance weight, so one person can carry things more steadily.",
        ),
    ],
    "marina": [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place where boats are kept in the water and people work near the docks.",
        ),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world set at a marina.")
    ap.add_argument("--place", choices=list(SETTINGS), default="marina")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", choices=list(OBJECTS), default="yoke")
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
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(HELPERS)
    obj = args.object or "yoke"
    return StoryParams(
        place=args.place,
        name=name,
        gender=gender,
        helper=helper,
        object=obj,
    )


def valid_story(params: StoryParams) -> bool:
    return params.place == "marina" and params.object == "yoke"


def reasonableness_gate(params: StoryParams) -> None:
    if not valid_story(params):
        raise StoryError("This storyworld only supports a quiet marina story with a yoke.")


def rhyme(line_a: str, line_b: str) -> str:
    return f"{line_a} {line_b}"


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_type = params.helper
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    yoke = world.add(Entity(
        id="yoke",
        kind="thing",
        type="tool",
        label="yoke",
        phrase="a small wooden yoke",
        owner=hero.id,
    ))
    world.facts = {"hero": hero, "helper": helper, "yoke": yoke, "params": params}
    return world


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    yoke: Entity = f["yoke"]

    world.say(f"At the marina, {hero.id} saw sleepy boats rocking in the hush of evening.")
    world.say(
        f"{hero.id} liked the little yoke because it could carry two pale pails, one on each side, "
        f"like a moonbeam in a tune."
    )
    world.say(f'"Can I use it?" {hero.id} asked, and {helper.label} smiled, "Yes, my dear, but carry it near."')

    world.para()
    world.say(f"{hero.id} lifted the yoke, but the rope slipped with a soft little click.")
    hero.memes["worry"] += 1
    hero.meters["lost"] += 1
    world.say(
        f"The pails wobbled toward the dock edge, and {hero.id} felt a tiny fright inside the night."
    )
    world.say(f'"Hold still," said {helper.label}. "If it tips, the water will sip!"')

    world.para()
    world.say(
        f"{hero.id} took a slow breath, then tied the rope in a snug little loop. "
        f'"One knot, not a lot," {hero.id} said, "and the yoke will rock, not flop."'
    )
    hero.memes["calm"] += 1
    hero.memes["joy"] += 1
    hero.meters["safe"] += 1
    yoke.meters["safe"] += 1
    world.say(
        f"The yoke stayed steady, the pails stayed near, and the marina grew quiet and clear."
    )
    world.say(
        f"{helper.label} gave a hug and whispered, "
        f'"Good night, little one. The work is done, and the moon says fun."'
    )

    world.facts["resolved"] = True
    world.facts["story_rhyme"] = True
    world.facts["dialogue"] = True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a gentle bedtime story set at a marina that includes the word "yoke".',
        f"Tell a short story where {p.name} and {p.helper} speak kindly about using a yoke by the water.",
        "Write a cozy rhyming bedtime story about a child, a small problem, and a calm fix at a marina.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Where is the story set?",
            answer="The story is set at a quiet marina with sleepy boats and wooden docks.",
        ),
        QAItem(
            question=f"What did {p.name} want to use?",
            answer=f"{p.name} wanted to use the yoke.",
        ),
        QAItem(
            question=f"Who talked with {p.name} about the yoke?",
            answer=f"{helper.label.capitalize()} talked with {p.name} and reminded {hero.pronoun('object')} to carry it carefully.",
        ),
        QAItem(
            question="What problem happened with the yoke?",
            answer="The rope slipped and the pails wobbled toward the dock edge, which made the child worry.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The child tied the rope in a snug loop, and the yoke stayed steady while everyone felt calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["marina"])
    out.extend(WORLD_KNOWLEDGE["yoke"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(marina, yoke).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    return asp.fact("place", "marina") + "\n" + asp.fact("object", "yoke")


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("marina", "yoke")}
    if atoms == py:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH:", atoms, py)
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = make_world(params)
    tell_story(world)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible stories:")
        for place, obj in asp_valid_stories():
            print(f"  {place} / {obj}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(place="marina", name="Mina", gender="girl", helper="mother", object="yoke")
        samples = [generate(params)]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
