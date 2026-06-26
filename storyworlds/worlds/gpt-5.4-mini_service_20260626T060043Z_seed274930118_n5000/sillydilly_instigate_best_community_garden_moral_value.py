#!/usr/bin/env python3
"""
A heartwarming story world set in a community garden.

Premise:
- A small group of neighbors is tending a shared garden.
- One character, nicknamed Sillydilly, keeps getting excited and trying to
  instigate a "best" idea: the biggest, fanciest, fastest garden plan.
- Another character worries because the plan could trample seedlings or make
  work uneven.
- The story turns when everyone slows down, talks kindly, and chooses a fair
  plan together.

Moral value:
- Respecting shared spaces matters.
- A good idea is not only the biggest idea; it is the one that helps everyone.

Reconciliation:
- The characters disagree at first, then repair the feeling with listening,
  apology, and cooperation.
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
class StoryParams:
    name: str = "Mira"
    helper: str = "June"
    garden_plot: str = "the community garden"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "character"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    plot: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming garden story world.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--helper", default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name_pool = ["Mira", "Lena", "Nico", "Ari", "Sage", "Toby"]
    helper_pool = ["June", "Owen", "Pia", "Iris", "Noah", "Mina"]
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice([n for n in helper_pool if n != name])
    return StoryParams(name=name, helper=helper, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = World(params.garden_plot)
    hero = world.add(Entity(id=params.name, label=params.name))
    helper = world.add(Entity(id=params.helper, label=params.helper))
    rake = world.add(Entity(id="rake", kind="thing", label="little rake"))
    seedlings = world.add(Entity(id="seedlings", kind="thing", label="seedlings"))

    hero.memes["pride"] = 1
    hero.memes["sillydilly"] = 1
    helper.memes["care"] = 1
    helper.meters["tired"] = 1

    world.say(
        f"{hero.id} was a cheerful helper at the community garden, and everyone "
        f"called {hero.pronoun('object')} Sillydilly when {hero.id} got extra excited."
    )
    world.say(
        f"{hero.id} wanted to instigate the best garden plan of all: a huge zigzag "
        f"path of bright pots and signs, even if the little seedlings had to move."
    )

    world.para()
    world.say(
        f"But {helper.id} looked at the tiny sprouts and said gently, "
        f"\"The best plan should help the whole garden, not just look biggest.\""
    )
    world.say(
        f"{hero.id} frowned at first. The idea sounded fun, and {hero.id} felt the tug "
        f"to push ahead anyway."
    )
    hero.memes["stubborn"] = 1
    helper.memes["worry"] = 1

    world.para()
    world.say(
        f"Then {helper.id} knelt beside the seedlings, handed over the little rake, "
        f"and asked {hero.id} to help make a softer path together."
    )
    world.say(
        f"{hero.id} paused, noticed the small green leaves, and felt a warm pinch of shame. "
        f"{hero.id} said sorry for trying to rush the garden."
    )
    hero.memes["reconciliation"] = 1
    helper.memes["forgive"] = 1

    world.para()
    world.say(
        f"After that, the two of them chose a kinder plan: tidy stepping stones, "
        f"watered rows, and a sign that welcomed everyone."
    )
    world.say(
        f"By sunset, {hero.id} was laughing again, {helper.id} was smiling, and the "
        f"community garden looked peaceful, useful, and bright."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        rake=rake,
        seedlings=seedlings,
        moral_value="best means kind and useful",
        reconciliation=True,
    )

    story = world.render()
    prompts = generation_prompts(world)
    story_qa = build_story_qa(world)
    world_qa = build_world_qa(world)
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    return [
        f'Write a heartwarming story set in a community garden about {hero}, called Sillydilly, and {helper}, who reconcile after a disagreement.',
        f"Tell a gentle story where {hero} wants to instigate the best plan, but learns that a shared garden needs kindness and cooperation.",
        f'Write a child-friendly story that includes the words "sillydilly", "instigate", and "best", and ends with reconciliation.',
    ]


def build_story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    return [
        QAItem(
            question=f"Who was called Sillydilly in the community garden?",
            answer=f"{hero} was called Sillydilly because {hero} got extra excited and tried to push the plan too fast."
        ),
        QAItem(
            question=f"What did {hero} want to instigate?",
            answer=f"{hero} wanted to instigate the best garden plan, with a big zigzag path and bright pots."
        ),
        QAItem(
            question=f"How did {hero} and {helper} fix their disagreement?",
            answer=f"They listened, said sorry, and chose a kinder plan together so the whole garden could benefit."
        ),
        QAItem(
            question="What moral value did the story show?",
            answer="The story showed that the best idea is the one that is kind, shared, and useful for everyone."
        ),
    ]


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a shared garden where neighbors grow plants and take care of the space together."
        ),
        QAItem(
            question="Why should people be gentle with seedlings?",
            answer="Seedlings are tiny young plants, so they can be easily bent or damaged if people are rough."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means fixing hurt feelings after a disagreement and becoming friendly again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: meters={ent.meters} memes={ent.memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "community_garden"),
            asp.fact("theme", "heartwarming"),
            asp.fact("value", "moral_value"),
            asp.fact("value", "reconciliation"),
            asp.fact("word", "sillydilly"),
            asp.fact("word", "instigate"),
            asp.fact("word", "best"),
        ]
    )


ASP_RULES = r"""
value_supported(moral_value) :- value(moral_value).
value_supported(reconciliation) :- value(reconciliation).
story_ok :- setting(community_garden), value_supported(moral_value), value_supported(reconciliation).
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = bool(model)
    if ok:
        print("OK: ASP gate recognizes the storyworld.")
        return 0
    print("MISMATCH: ASP gate failed.")
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


CURATED = [
    StoryParams(name="Mira", helper="June"),
    StoryParams(name="Nico", helper="Iris"),
    StoryParams(name="Sage", helper="Owen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("ASP OK" if model else "ASP FAIL")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
