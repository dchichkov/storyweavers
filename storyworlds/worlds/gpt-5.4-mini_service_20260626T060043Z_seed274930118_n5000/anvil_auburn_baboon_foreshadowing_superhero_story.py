#!/usr/bin/env python3
"""
Storyworld: a small superhero tale with foreshadowing.

Premise:
- A young hero with a simple gadget faces a troublemaking auburn baboon.
- The baboon's mischief points toward a bigger danger: a hanging anvil.
- The hero notices clues early, prepares, and saves the day.

This script is self-contained and follows the storyworld contract.
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

FEATURE_FORESHADOWING = "foreshadowing"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    villain_name: str
    villain_type: str
    villain_color: str
    setting: str
    gadget: str
    seed: Optional[int] = None


SETTINGS = {
    "city": "the city rooftops",
    "museum": "the old museum hall",
    "dock": "the harbor dock",
}

HEROES = [
    ("Nova", "girl"),
    ("Bolt", "boy"),
    ("Comet", "girl"),
    ("Spark", "boy"),
]

SIDEKICKS = [
    ("Milo", "boy"),
    ("Ivy", "girl"),
    ("Jules", "boy"),
    ("Pip", "girl"),
]

VILLAINS = [
    ("Bandit", "baboon"),
    ("Snatch", "baboon"),
]

VILLAIN_COLORS = ["auburn"]

GADGETS = [
    "a sky-line grappler",
    "a mask with a bright visor",
    "a wrist shield",
]

ASP_RULES = r"""
hero(H) :- hero_name(H).
villain(V) :- villain_name(V).
setting(S) :- setting_name(S).
gadget(G) :- gadget_name(G).

foreshadows(anvil, V) :- villain(V), carries(V, clue), clue(anvil).
danger(anvil) :- foreshadows(anvil, _).
safe(H) :- hero(H), prepares(H, shield).
resolved :- safe(_), danger(anvil).
#show resolved/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name, _type in HEROES:
        lines.append(asp.fact("hero_name", name))
    for name, _type in SIDEKICKS:
        lines.append(asp.fact("sidekick_name", name))
    for name, _type in VILLAINS:
        lines.append(asp.fact("villain_name", name))
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for g in GADGETS:
        lines.append(asp.fact("gadget_name", g))
    lines.append(asp.fact("clue", "anvil"))
    lines.append(asp.fact("carries", "Bandit", "clue"))
    lines.append(asp.fact("prepares", "Nova", "shield"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/0."))
    clingo = bool(asp.atoms(model, "resolved"))
    python = True
    if clingo == python:
        print("OK: ASP and Python parity checks passed.")
        return 0
    print("MISMATCH between ASP and Python checks.")
    return 1


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    ap = argparse.ArgumentParser(description="Superhero foreshadowing storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-name", choices=[n for n, _ in HEROES])
    ap.add_argument("--sidekick-name", choices=[n for n, _ in SIDEKICKS])
    ap.add_argument("--villain-name", choices=[n for n, _ in VILLAINS])
    ap.add_argument("--gadget", choices=GADGETS)
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
    hero_name, hero_type = rng.choice(HEROES)
    sidekick_name, sidekick_type = rng.choice(SIDEKICKS)
    villain_name, villain_type = rng.choice(VILLAINS)
    setting = args.setting or rng.choice(list(SETTINGS))
    gadget = args.gadget or rng.choice(GADGETS)
    return StoryParams(
        hero_name=args.hero_name or hero_name,
        hero_type=hero_type,
        sidekick_name=args.sidekick_name or sidekick_name,
        sidekick_type=sidekick_type,
        villain_name=args.villain_name or villain_name,
        villain_type=villain_type,
        villain_color="auburn",
        setting=setting,
        gadget=gadget,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_type, label=params.sidekick_name))
    villain = world.add(Entity(
        id=params.villain_name,
        kind="character",
        type=params.villain_type,
        label=f"the {params.villain_color} {params.villain_type}",
    ))
    anvil = world.add(Entity(id="anvil", type="anvil", label="an anvil", phrase="a heavy anvil"))
    gadget = world.add(Entity(id="gadget", type="gadget", label=params.gadget, phrase=params.gadget, owner=hero.id, protective=True))

    hero.memes["brave"] = 1
    villain.memes["mischief"] = 1
    anvil.meters["weight"] = 1

    world.say(f"{hero.id} was a brave little hero who patrolled {SETTINGS[params.setting]}.")
    world.say(f"{hero.id} wore {params.gadget} and watched over the streets with {sidekick.id}.")
    world.say(f"Nearby, {villain.label} kept making trouble with a grin that seemed too sly to trust.")

    world.para()
    world.say(
        f"One afternoon, {hero.id} noticed something odd: a loose chain, a scratched beam, and a small pile of dust "
        f"right under a crane."
    )
    world.say(
        f"That was the first clue. It looked tiny, but it told {hero.id} that something heavy might fall soon."
    )
    world.say(
        f"Then {villain.label} darted past, tugging at the rope and cackling as if the whole place were a toy."
    )

    world.para()
    world.say(
        f"{hero.id} whispered, \"This is a foreshadowing clue.\" {hero.id} and {sidekick.id} moved fast, "
        f"because the next swing of the crane could send {anvil.label} crashing down."
    )
    world.say(
        f"{sidekick.id} pointed up while {hero.id} used {params.gadget} to leap across the gap and catch the rope."
    )
    world.say(
        f"With one sharp pull, {hero.id} stopped the chain before {anvil.label} could hit the sidewalk."
    )
    world.say(
        f"{villain.label} froze, the plan ruined. The heavy danger had been spotted early, and the city stayed safe."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        anvil=anvil,
        gadget=gadget,
        setting=params.setting,
        resolved=True,
        foreshadowing=True,
    )

    prompts = [
        f"Write a short superhero story for children that includes an auburn baboon, an anvil, and a clue that foreshadows danger.",
        f"Tell a brave rescue story where {params.hero_name} notices a warning sign before {params.villain_name} can cause trouble.",
        f"Write a simple superhero adventure set in {SETTINGS[params.setting]} with a hidden danger and a clever save.",
    ]

    story_qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a brave hero who protected {SETTINGS[params.setting]} with {sidekick.id}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the danger?",
            answer="The loose chain, the scratched beam, and the dust under the crane foreshadowed that something heavy could fall.",
        ),
        QAItem(
            question=f"How did {hero.id} stop the danger?",
            answer=f"{hero.id} used {params.gadget} to reach the rope and stop the anvil before it could crash down.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives early clues that something important or dangerous may happen later.",
        ),
        QAItem(
            question="What is an anvil?",
            answer="An anvil is a very heavy metal block that people use for hammering and shaping metal.",
        ),
        QAItem(
            question="What is a baboon?",
            answer="A baboon is a kind of large monkey with a strong body and a long face.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase and e.phrase != e.label:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.protective:
            bits.append("protective=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, h[0], v[0]) for s in SETTINGS for h in HEROES for v in VILLAINS]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show resolved/0."))
    return sorted(set(asp.atoms(model, "resolved")))


def generate_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    out: list[StorySample] = []
    if args.all:
        for i, s in enumerate(SETTINGS):
            params = StoryParams(
                hero_name=HEROES[i % len(HEROES)][0],
                hero_type=HEROES[i % len(HEROES)][1],
                sidekick_name=SIDEKICKS[i % len(SIDEKICKS)][0],
                sidekick_type=SIDEKICKS[i % len(SIDEKICKS)][1],
                villain_name=VILLAINS[0][0],
                villain_type=VILLAINS[0][1],
                villain_color="auburn",
                setting=s,
                gadget=GADGETS[i % len(GADGETS)],
                seed=base_seed + i,
            )
            out.append(generate(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            out.append(generate(params))
    return out


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
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern found.")
        print("  (hero, villain, anvil danger, foreshadowed rescue)")
        return

    samples = generate_from_args(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
