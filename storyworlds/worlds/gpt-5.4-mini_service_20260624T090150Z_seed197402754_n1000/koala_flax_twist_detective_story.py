#!/usr/bin/env python3
"""
Storyworld: koala_flax_twist_detective_story
A small detective-story domain about a koala, flax, and a twist.
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

TITLE = "Koala, Flax, and the Twist"


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"koala"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    place: str = "the little museum"
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    clue_spots: list[str]
    twist_device: str


SETTINGS = {
    "museum": Setting(place="the little museum", clue_spots=["front desk", "archive room", "display hall"], twist_device="spindle"),
    "mill": Setting(place="the old mill", clue_spots=["loading dock", "thread room", "loft"], twist_device="wheel"),
    "garden": Setting(place="the moonlit garden", clue_spots=["hedge path", "pumpkin patch", "tool shed"], twist_device="vine"),
}

NAMES = ["Kip", "Koko", "Milo", "Jasper", "Tala"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


def build_world(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(id="Koala", kind="character", type="koala", label="Koala"))
    hero.name = rng.choice(NAMES)  # type: ignore[attr-defined]
    hero.meters["attention"] = 1
    hero.memes["curiosity"] = 1
    hero.memes["calm"] = 1

    chief = world.add(Entity(id="Chief", kind="character", type="person", label="the chief"))
    witness = world.add(Entity(id="Witness", kind="character", type="person", label="the witness"))

    flax = world.add(Entity(
        id="Flax",
        kind="thing",
        type="flax",
        label="flax bundle",
        phrase="a soft bundle of pale flax",
        owner="Museum",
    ))
    twist = world.add(Entity(
        id="Twist",
        kind="thing",
        type="twist",
        label="twist mark",
        phrase="a tight twist in the fibers",
        owner="Flax",
    ))

    world.facts.update(hero=hero, chief=chief, witness=witness, flax=flax, twist=twist)
    return world


def _suspect_clue(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    flax: Entity = world.facts["flax"]  # type: ignore[assignment]
    chief: Entity = world.facts["chief"]  # type: ignore[assignment]
    witness: Entity = world.facts["witness"]  # type: ignore[assignment]

    world.say(
        f"In {world.setting.place}, Koala was the best little detective in town. "
        f"{hero.pronoun().capitalize()} liked quiet clues, neat paws, and cases that began with a missing thing."
    )
    world.say(
        f"One morning, {chief.label} pointed at the worktable. "
        f'"The flax bundle is gone," {chief.label} said. "We need it back before dusk."'
    )
    world.say(
        f"Koala found a pale thread near the floor and touched it with careful paws. "
        f"{witness.label.capitalize()} whispered that the thread had a strange twist in it."
    )
    world.facts["clue_spot"] = world.setting.clue_spots[1]


def _investigate(world: World) -> None:
    flax: Entity = world.facts["flax"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    world.para()
    world.say(
        f"Koala padded from the front desk to the {world.facts['clue_spot']}. "
        f"{hero.pronoun().capitalize()} sniffed the air, then inspected the twisted fiber."
    )
    flax.meters["unfolded"] = 1
    flax.memes["mystery"] = 1
    world.say(
        f"The clue was not torn. It was tied in a tiny twist, like someone had wound it on purpose."
    )
    world.say(
        f"Koala's ears rose. A thief would have rushed away, but this twist looked careful."
    )


def _turn(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    chief: Entity = world.facts["chief"]  # type: ignore[assignment]
    flax: Entity = world.facts["flax"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"Koala followed the twist to the loft. There, the bundle hung beside a little open window."
    )
    world.say(
        f"A baby bird chirped outside, stuck on a windy ledge. The flax had been twisted into a soft rescue line."
    )
    world.say(
        f'{chief.label} blinked. "So nobody stole it?" {chief.label} asked.'
    )
    world.say(
        f"Koala shook {hero.pronoun('possessive')} head. {flax.label.capitalize()} had been borrowed, not stolen."
    )
    world.facts["twist_revealed"] = True
    world.facts["missing_reason"] = "rescue line"


def _resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    chief: Entity = world.facts["chief"]  # type: ignore[assignment]
    flax: Entity = world.facts["flax"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"Together, Koala and {chief.label} used the flax to help the baby bird down safely."
    )
    world.say(
        f"After that, the bundle was neatly rewound. The twist stayed in the story, but not in the blame."
    )
    world.say(
        f"Koala smiled as {hero.pronoun('possessive')} casebook snapped shut. "
        f"The missing flax had become a rescue, and that was the best ending of all."
    )
    flax.meters["returned"] = 1
    hero.memes["pride"] = 1
    chief.memes["relief"] = 1


def tell_story(params: StoryParams, rng: random.Random) -> World:
    world = build_world(params, rng)
    _suspect_clue(world)
    _investigate(world)
    _turn(world)
    _resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short detective story for a small child about a koala, a flax bundle, and a twist.",
        f"Tell a gentle mystery where Koala investigates missing flax at {world.setting.place}.",
        "Write a simple story where the clue seems like a theft, but the twist is kinder than it looks.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    chief: Entity = world.facts["chief"]  # type: ignore[assignment]
    flax: Entity = world.facts["flax"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who was the detective in the story?",
            answer=f"The detective was Koala, the little koala who liked solving quiet mysteries.",
        ),
        QAItem(
            question="What went missing at first?",
            answer=f"The flax bundle went missing at first, so {chief.label} asked Koala to investigate.",
        ),
        QAItem(
            question="Why did the flax look suspicious?",
            answer="It looked suspicious because there was a tiny twist in the fibers, which made it seem like someone had hidden it.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that nobody stole the flax. It had been borrowed to make a rescue line for a baby bird.",
        ),
        QAItem(
            question="How did the story end?",
            answer="Koala helped use the flax to save the baby bird, and then the bundle was put back neatly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is flax?",
            answer="Flax is a plant fiber people can spin into thread or rope.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a turning or winding shape. Twists can be found in rope, thread, and stories too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is suspicious when the twist is present.
suspicious(clue) :- twist(clue).

% The case is solved when the flax is explained by a rescue reason.
solved(case) :- flax(case), rescue_reason(case).

#show suspicious/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("flax", "case"),
            asp.fact("twist", "clue"),
            asp.fact("rescue_reason", "case"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspicious/1.\n#show solved/1."))
    atoms = {f"{sym.name}({','.join(str(a) for a in sym.arguments)})" for sym in model}
    expected = {"suspicious(clue)", "solved(case)"}
    if atoms == expected:
        print("OK: ASP twin matches the story logic.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny koala detective storyworld with flax and a twist.")
    ap.add_argument("--place", choices=SETTINGS, default="museum")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(place=args.place, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    world = tell_story(params, rng)
    story = world.render()
    sample = StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


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
        print(asp_program("#show suspicious/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspicious/1.\n#show solved/1."))
        print("ASP atoms:", sorted(f"{sym.name}({','.join(str(a) for a in sym.arguments)})" for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, place in enumerate(SETTINGS):
            p = StoryParams(place=place, seed=base_seed + i)
            samples.append(generate(p))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
