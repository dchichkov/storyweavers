#!/usr/bin/env python3
"""
A small pirate-tale story world with a cautionary turn, a sharing fix, and a
light humorous ending.

Seed premise:
- A little pirate sees a trouble spot with one eyed caution.
- The crew wants a shared treasure snack.
- A careless choice could spoil the loot.
- The captain warns, they share wisely, and the joke lands safely.
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

ASP_RULES = r"""
eyed(X) :- pirate(X), has_eye(X, one).
cautionary_scene(P) :- pirate(P), sees_warning(P).
sharing_scene(C) :- crew(C), has_treasure(C), shares(C).
humor_scene(P) :- pirate(P), jokes(P), nobody_splashes(P).
safe_story(P) :- cautionary_scene(P), sharing_scene(P), humor_scene(P).
"""

PIRATE_NAMES = ["Mara", "Jett", "Nico", "Luna", "Ivo", "Pip", "Rae", "Sail"]
CREW_NAMES = ["Captain Brine", "First Mate Wren", "Bosun Tilly", "Deckhand Oat"]
SCENES = ["dock", "cove", "deck", "island shore"]
TREASURES = ["golden pear", "sweet biscuit", "berry tart", "shiny apple"]
TREATS = ["crumbly bun", "salted plum", "tiny cake", "honey toast"]


@dataclass
class Character:
    id: str
    role: str
    eyed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"


@dataclass
class Setting:
    place: str = "the moonlit dock"


@dataclass
class StoryParams:
    name: str
    crew: str
    place: str
    treasure: str
    treat: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Character
    crew: Character
    shared_treasure: str
    shared_treat: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with caution, sharing, and humor.")
    ap.add_argument("--name", choices=PIRATE_NAMES)
    ap.add_argument("--crew", choices=CREW_NAMES)
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--treat", choices=TREATS)
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("pirate", "hero"), asp.fact("crew", "crew"), asp.fact("has_eye", "hero", "one")]
    lines += [asp.fact("has_treasure", "crew"), asp.fact("shares", "crew"), asp.fact("jokes", "hero"), asp.fact("sees_warning", "hero")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/1."))
    atoms = set(asp.atoms(model, "safe_story"))
    expected = {("hero",)}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(PIRATE_NAMES),
        crew=args.crew or rng.choice(CREW_NAMES),
        place=args.place or rng.choice(SCENES),
        treasure=args.treasure or rng.choice(TREASURES),
        treat=args.treat or rng.choice(TREATS),
    )


def make_world(params: StoryParams) -> World:
    hero = Character(id=params.name, role="pirate", eyed=True, meters={"caution": 1.0}, memes={"humor": 0.5})
    crew = Character(id=params.crew, role="crew", eyed=False, meters={"sharing": 1.0}, memes={"kindness": 1.0})
    return World(setting=Setting(place=f"the {params.place}"), hero=hero, crew=crew,
                 shared_treasure=params.treasure, shared_treat=params.treat)


def tell(world: World) -> None:
    h, c = world.hero, world.crew
    world.say(f"At {world.setting.place}, {h.id} was an eyed little pirate who noticed a tricky plank before anyone else.")
    world.say(f"{h.id} saw the old board lean and warned the crew, because a pirate with one eye can spot trouble fast.")
    world.para()
    world.say(f"The crew wanted to split {world.shared_treasure}, but {h.id} nearly grabbed it all at once.")
    world.say(f"{c.id} lifted a hand and said the best loot is shared, not snatched.")
    world.say(f"So they passed around {world.shared_treat}, and each pirate got a fair bite.")
    world.para()
    world.say(f"{h.id} laughed and said, \"I eyed the warning and learned my lesson.\"")
    world.say(f"Then the crew joked that the plank was so old it looked ready to join the captain's boots, and everyone chuckled as the moonlight shone on their shared snack.")
    world.facts.update(hero=h, crew=c, setting=world.setting)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short pirate tale for children about an eyed pirate who spots danger, learns to share, and ends with a joke.",
        f"Tell a cautionary story where {f['hero'].id} at {f['setting'].place} learns to share {world.shared_treasure} with {f['crew'].id}.",
        f"Write a playful pirate story that includes the word 'eyed' and ends with everyone sharing {world.shared_treat}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, c = world.hero, world.crew
    return [
        QAItem(
            question=f"Who noticed the danger first at {world.setting.place}?",
            answer=f"{h.id} noticed it first. {h.id} was the eyed pirate, so the warning stood out right away.",
        ),
        QAItem(
            question=f"What did the pirates decide to do with {world.shared_treasure}?",
            answer=f"They decided to share {world.shared_treasure} instead of taking it all at once.",
        ),
        QAItem(
            question=f"Why did the ending feel funny?",
            answer=f"It felt funny because the crew joked about the old plank and laughed together after sharing {world.shared_treat}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be eyed?",
            answer="In this story, eyed means the pirate has one eye and watches carefully, so they can spot trouble early.",
        ),
        QAItem(
            question="Why should pirates share treasure?",
            answer="Pirates should share treasure so everyone gets a fair part and the crew stays happy.",
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can help because a small joke can ease tension and leave the ending feeling warm and cheerful.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"hero={world.hero.id} role={world.hero.role} eyed={world.hero.eyed} meters={world.hero.meters} memes={world.hero.memes}",
        f"crew={world.crew.id} role={world.crew.role} meters={world.crew.meters} memes={world.crew.memes}",
        f"place={world.setting.place}",
        f"treasure={world.shared_treasure}",
        f"treat={world.shared_treat}",
    ])


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mara", crew="Captain Brine", place="dock", treasure="golden pear", treat="honey toast"),
        StoryParams(name="Pip", crew="First Mate Wren", place="cove", treasure="sweet biscuit", treat="tiny cake"),
        StoryParams(name="Nico", crew="Bosun Tilly", place="deck", treasure="berry tart", treat="salted plum"),
        StoryParams(name="Luna", crew="Deckhand Oat", place="island shore", treasure="shiny apple", treat="crumbly bun"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show eyed/1.\n#show cautionary_scene/1.\n#show sharing_scene/1.\n#show humor_scene/1.\n#show safe_story/1."))
        print("\n".join(str(a) for a in model))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i if args.seed is not None else None
            samples.append(generate(p))

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
