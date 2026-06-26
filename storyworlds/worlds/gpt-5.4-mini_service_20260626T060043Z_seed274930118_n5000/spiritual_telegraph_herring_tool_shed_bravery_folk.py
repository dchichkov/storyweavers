#!/usr/bin/env python3
"""
A tiny folk-tale storyworld: a child in a tool shed hears a spiritual
telegraph knock and finds bravery with a herring-shaped charm.

The world is deliberately small and constraint-checked:
- the tool shed is the setting
- the telegraph signal carries a message that matters
- the herring is the humble object that becomes the turn
- bravery is the emotional turn that resolves the tale
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the tool shed"
    indoor: bool = True
    affordances: set[str] = field(default_factory=lambda: {"telegraph", "herring", "spiritual"})


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTINGS = {
    "tool_shed": Setting(place="the tool shed", indoor=True),
}

HERO_NAMES = ["Mira", "Hank", "Elsie", "Toby", "Anya", "Nell"]
PARENT_TYPES = ["mother", "father", "grandmother", "grandfather"]


def tell(hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(SETTINGS["tool_shed"])
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    telegraph = world.add(Entity(
        id="telegraph",
        label="old telegraph",
        phrase="an old telegraph with a brass key",
    ))
    herring = world.add(Entity(
        id="herring",
        label="herring charm",
        phrase="a silver herring charm wrapped in blue thread",
        owner=hero.id,
    ))
    spirit = world.add(Entity(
        id="spirit",
        label="spiritual whisper",
        phrase="a spiritual whisper",
    ))

    # Act 1: the setup.
    world.say(
        f"In the tool shed, {hero_name} was a little {hero_type} who loved quiet things and bright tales."
    )
    world.say(
        f"{hero.pronoun().capitalize()} found {herring.phrase} beside {telegraph.phrase}, and {hero_name} felt it was meant for {hero.pronoun('object')}."
    )
    hero.memes["wonder"] = 1.0
    herring.meters["kept_safe"] = 1.0

    world.para()

    # Act 2: the message and the worry.
    world.say(
        f"Then the old telegraph gave a soft tap, and the shed seemed full of a spiritual hush."
    )
    world.say(
        f"A tiny voice seemed to say, 'Only the brave may carry the message beyond the shed door.'"
    )
    hero.memes["fear"] = 1.0
    hero.memes["bravery"] = 0.0
    world.say(
        f"{hero_name} wanted to answer, but {hero.pronoun('possessive')} knees felt shaky."
    )
    world.say(
        f"{parent_type.capitalize()} said, 'A brave heart can begin small, like a herring that gleams in the dark.'"
    )

    world.para()

    # Act 3: turn and resolution.
    hero.memes["bravery"] = 1.0
    hero.memes["fear"] = 0.0
    spirit.meters["heard"] = 1.0
    world.say(
        f"So {hero_name} took a deep breath, held the herring charm tight, and knocked the telegraph key once more."
    )
    world.say(
        f"The little knock sounded steady now, and the spiritual whisper turned warm, as if it had been waiting for courage."
    )
    world.say(
        f"{hero_name} smiled, because {hero.pronoun()} had learned that bravery could be small, plain, and still strong enough to carry a message."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        telegraph=telegraph,
        herring=herring,
        spirit=spirit,
        brave=True,
        place=world.setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short folk tale set in a tool shed, with a spiritual telegraph message and a brave little herring charm.',
        f"Tell a gentle story about {hero.id} finding courage in {world.setting.place}.",
        "Write a simple folk tale where a child hears a spiritual knock from an old telegraph and learns bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {world.setting.place}, where the old tools were sleeping and the telegraph could still whisper."
        ),
        QAItem(
            question=f"What did {hero.id} find in the shed?",
            answer=f"{hero.id} found a herring charm and an old telegraph with a brass key."
        ),
        QAItem(
            question=f"How did {hero.id} become brave?",
            answer=f"{hero.id} became brave by taking a deep breath, holding the herring charm, and tapping the telegraph key again."
        ),
        QAItem(
            question=f"What did {parent.type} say to help?",
            answer="The parent said that a brave heart can begin small, like a herring that gleams in the dark."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a telegraph?",
            answer="A telegraph is a machine that sends messages by making clicks or taps."
        ),
        QAItem(
            question="What is a herring?",
            answer="A herring is a small silvery fish, often known for its shiny body."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel scared."
        ),
        QAItem(
            question="What is a tool shed?",
            answer="A tool shed is a small building where people keep tools and supplies."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(tool_shed).
affords(tool_shed, telegraph).
affords(tool_shed, herring).
affords(tool_shed, spiritual).

brave(hero) :- has(hero, bravery), not has(hero, fear).
message(telegraph).
symbol(herring).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", "tool_shed")]
    lines.append(asp.fact("affords", "tool_shed", "telegraph"))
    lines.append(asp.fact("affords", "tool_shed", "herring"))
    lines.append(asp.fact("affords", "tool_shed", "spiritual"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale storyworld in a tool shed.")
    ap.add_argument("--place", choices=list(SETTINGS))
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
    place = args.place or "tool_shed"
    if place != "tool_shed":
        raise StoryError("This tiny world only knows the tool shed.")
    return StoryParams(
        place=place,
        hero_name=rng.choice(HERO_NAMES),
        hero_type=rng.choice(["girl", "boy"]),
        parent_type=rng.choice(PARENT_TYPES),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.hero_name, params.hero_type, params.parent_type)
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

    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story shape: tool_shed with telegraph, herring, and spiritual.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="tool_shed",
            hero_name="Mira",
            hero_type="girl",
            parent_type="grandmother",
            seed=base_seed,
        )
        samples = [generate(params)]
    else:
        for i in range(max(1, args.n)):
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
