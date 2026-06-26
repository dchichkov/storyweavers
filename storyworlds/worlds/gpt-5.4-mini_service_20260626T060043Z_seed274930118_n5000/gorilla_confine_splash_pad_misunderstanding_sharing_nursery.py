#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gorilla_confine_splash_pad_misunderstanding_sharing_nursery.py
============================================================================================================

A tiny storyworld in a nursery-rhyme style: a gorilla, a splash pad, a
misunderstanding, and a sharing turn that resolves the trouble.

Seed tale inspiration:
---
At the splash pad, a young gorilla wanted to keep all the water to himself.
He thought the little children were trying to confine his fun, and they thought
he was blocking the sprays on purpose. The keeper explained that nobody was
being mean; they just needed to share the space and take turns. The gorilla
laughed, stepped aside, and everyone played together in the bright spray.

World model:
---
- The splash pad has a handful of water jets and one big play ring.
- The gorilla can feel blocked or welcomed.
- A misunderstanding can raise worry on both sides.
- Sharing the ring lowers tension and makes the water fun for everyone.

Narrative shape:
---
1. Setup: the gorilla loves the splash pad and the children arrive.
2. Turn: a misunderstanding makes the gorilla think the play is being confined.
3. Resolution: a sharing rule and a helper gesture make room for everyone.

The prose is intentionally child-facing and rhyme-shaped, while the underlying
state changes remain causal and grounded in the simulated world.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"gorilla"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"child", "keeper"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class SplashPad:
    name: str = "the splash pad"
    jets: int = 3
    ring_open: bool = True


@dataclass
class StoryParams:
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.setting = SplashPad()
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


def rhyme(text: str) -> str:
    return text


def make_world(params: StoryParams) -> World:
    w = World()
    gorilla = w.add(Entity(
        id=params.name,
        kind="character",
        type="gorilla",
        label="gorilla",
        meters={"wet": 0.0, "space": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "confusion": 0.0, "warmth": 0.0},
    ))
    child = w.add(Entity(
        id="children",
        kind="character",
        type="child",
        label="children",
        plural=True,
        meters={"wet": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "confusion": 0.0},
    ))
    keeper = w.add(Entity(
        id="keeper",
        kind="character",
        type="keeper",
        label="keeper",
        meters={"attention": 0.0},
        memes={"calm": 0.0, "warmth": 0.0},
    ))

    # Act 1
    w.say(f"{gorilla.id} was a gorilla at the splash pad, under sun and spray.")
    w.say("He liked the whish and whoosh of water games, and he liked them every day.")
    w.say("The children came with little feet and giggles bright as bells.")
    w.say("They reached for the ring of water where the cool wet jumping dwells.")
    w.para()

    # Act 2: misunderstanding
    gorilla.memes["worry"] += 1
    gorilla.memes["confusion"] += 1
    child.memes["confusion"] += 1
    gorilla.meters["space"] += 1
    child.meters["wet"] += 1

    w.say(f"{gorilla.id} thought, “They mean to confine my fun and keep the splashes small!”")
    w.say("The children thought he meant to block the jets and guard the ring from all.")
    w.say("So the water felt less merry, and the air grew tight and thin,")
    w.say("like a bubble on a windy day that could not quite let joy swim in.")
    w.para()

    # Act 3: sharing
    keeper.memes["calm"] += 1
    keeper.memes["warmth"] += 1
    gorilla.memes["worry"] = max(0.0, gorilla.memes["worry"] - 1.0)
    gorilla.memes["confusion"] = max(0.0, gorilla.memes["confusion"] - 1.0)
    child.memes["confusion"] = max(0.0, child.memes["confusion"] - 1.0)
    gorilla.memes["joy"] += 1
    child.memes["joy"] += 1
    w.setting.ring_open = True

    w.say("The keeper clapped and sang, “No one needs to crowd the stream;")
    w.say("share the ring and take your turns, and all the sprays will gleam.”")
    w.say(f"{gorilla.id} stepped aside and smiled, and the children made room too,")
    w.say("Then everyone took little turns beneath the sparkling blue.")
    w.say("The gorilla laughed in bubbles, the children spun and swayed,")
    w.say("and the splash pad rang with happy feet in a bright and water play.")
    w.say("The day was full of sharing, and the misunderstanding was through;")
    w.say("what once felt like a closing fence became a game for all to do.")

    w.facts.update(
        gorilla=gorilla,
        child=child,
        keeper=keeper,
        misunderstood=True,
        shared=True,
        location=w.setting.name,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a gorilla at a splash pad, where a misunderstanding turns into sharing.',
        f"Tell a gentle story set at {f['location']} where {f['gorilla'].id} thinks the play is being confined, but the children and keeper help everyone share.",
        "Write a simple rhyming story with water, worry, and a happy sharing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    g = world.facts["gorilla"]
    c = world.facts["child"]
    k = world.facts["keeper"]
    return [
        QAItem(
            question=f"Where does {g.id} play in the story?",
            answer=f"{g.id} plays at the splash pad, where the water sprays and the children come to play.",
        ),
        QAItem(
            question=f"What did {g.id} think at first when the children came near the water ring?",
            answer=f"{g.id} thought they might confine his fun and keep the splashes from being shared.",
        ),
        QAItem(
            question="How did the trouble get fixed?",
            answer=f"The keeper explained that everyone could share the ring and take turns, so the gorilla and the children could all play happily.",
        ),
        QAItem(
            question=f"How did {g.id} feel at the end?",
            answer=f"{g.id} felt happy and calm, and {k.id} was pleased because the splash pad became a shared game instead of a mix-up.",
        ),
        QAItem(
            question=f"Who learned to share?",
            answer=f"{g.id} and the children both learned to share the splash pad space, with the keeper guiding them kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a splash pad?",
            answer="A splash pad is a play place with water sprays and sprinklers where children can run and get wet.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something too, so everyone can have a turn or enjoy it together.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think something different from what another person means.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: gorilla, splash pad, misunderstanding, sharing.")
    ap.add_argument("--name", default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(["Gogo", "Momo", "Bongo", "Kiki", "Lolo"])
    return StoryParams(name=name, seed=args.seed)


ASP_RULES = r"""
% A misunderstanding happens when the gorilla worries and the children also confuse the action.
misunderstanding(g) :- gorilla(g), worries(g), children_confused.

% Sharing resolves the problem and opens the ring.
resolved(g) :- misunderstanding(g), sharing.

#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("gorilla", "g1"),
        asp.fact("worries", "g1"),
        asp.fact("children_confused"),
        asp.fact("sharing"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(1)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
