#!/usr/bin/env python3
"""
A small superhero-style story world set in a reading nook, where a playful
brontosaurus can cause damage, and humor, dialogue, and magic turn the problem
into a gentle win.
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

    def pronoun(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "she"
        if self.type in {"boy", "man", "father"}:
            return "he"
        return "they"

    def obj(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "her"
        if self.type in {"boy", "man", "father"}:
            return "him"
        return "them"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    villain_name: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


SETTING = "the reading nook"

HEROES = [
    ("Mira", "girl"),
    ("Toby", "boy"),
    ("Nova", "girl"),
    ("Finn", "boy"),
]

SIDEKICKS = [
    ("Bean", "cat"),
    ("Pip", "robot"),
    ("Dot", "dog"),
    ("Zuzu", "bird"),
]

VILLAINS = [
    "the wobble-brontosaurus",
    "the giggle-brontosaurus",
    "the sleepy brontosaurus",
]

ASP_RULES = r"""
% damage happens when the brontosaurus bumps the shelf or rug
damage(D) :- brontosaurus(D), bump(D), not shielded(D).
resolved :- damage(damage), magic_used, laugh_shared.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "reading_nook"),
        asp.fact("feature", "humor"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "magic"),
        asp.fact("thing", "bookshelf"),
        asp.fact("thing", "soft_rug"),
        asp.fact("thing", "reading_lamp"),
        asp.fact("brontosaurus", "damage"),
        asp.fact("bump", "damage"),
        asp.fact("damage", "damage"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_damage_possible() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show damage/1. #show resolved/0."))
    return any(sym.name == "damage" for sym in model)


def reasonableness_gate() -> None:
    if not asp_damage_possible():
        raise StoryError("No story: the brontosaurus must be able to cause real damage before a magic fix matters.")


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick_type, label=params.sidekick_name))
    villain = world.add(Entity(id="villain", kind="character", type="brontosaurus", label=params.villain_name))
    shelf = world.add(Entity(id="shelf", type="thing", label="the tall bookshelf", meters={"damage": 0}))
    rug = world.add(Entity(id="rug", type="thing", label="the soft rug", meters={"damage": 0}))
    lamp = world.add(Entity(id="lamp", type="thing", label="the reading lamp", meters={"damage": 0}))

    hero.memes["hope"] = 1
    sidekick.memes["humor"] = 1
    villain.memes["restless"] = 1

    world.say(
        f"In {SETTING}, {hero.label} liked to read by the lamp while {sidekick.label} "
        f"watched the pages turn."
    )
    world.say(
        f"They called themselves the Reading Nook Rescue Team, because even quiet places "
        f"sometimes needed heroes."
    )

    world.para()
    world.say(
        f"Then {villain.label} squeezed between the beanbag and the shelf, and the floor gave a tiny groan."
    )
    world.say(
        f'"Oops," {villain.label} said. "My tail has superhero size."'
    )
    shelf.meters["damage"] += 1
    rug.meters["damage"] += 1
    lamp.meters["damage"] += 0

    world.para()
    world.say(
        f'{hero.label} gasped, but {sidekick.label} grinned. "This is not a disaster," '
        f'{sidekick.label} said. "It is a wiggly-dino problem."'
    )
    hero.memes["worry"] = 1
    sidekick.memes["humor"] = 2
    world.say(
        f'{hero.label} asked, "How do we fix it?"'
    )
    world.say(
        f'"With a magic blanket," said {villain.label}. "And maybe fewer tail twirls."'
    )

    world.para()
    world.say(
        f'{hero.label} lifted a sparkly bookmark, and the bookmark flashed like a tiny star.'
    )
    world.say(
        f'"Magic, mend!" {hero.label} said.'
    )
    shelf.meters["damage"] = 0
    rug.meters["damage"] = 0
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        villain=villain,
        shelf=shelf,
        rug=rug,
        lamp=lamp,
        damage_fixed=True,
        place=SETTING,
    )
    world.say(
        f"The bookshelf stood straight again, the rug smoothed out, and {villain.label} sat carefully on the floor."
    )
    world.say(
        f'{sidekick.label} laughed. "Best rescue ever," {sidekick.label} said, and everyone curled up to read.'
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story for a young child set in a reading nook, with humor, dialogue, and magic.',
        f"Tell a gentle story where {f['hero'].label} and {f['sidekick'].label} handle damage caused by {f['villain'].label}.",
        'Write a child-friendly story in a reading nook where a brontosaurus problem is solved with a magical fix and funny conversation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    villain = f["villain"]
    return [
        QAItem(
            question=f"Where does the story take place?",
            answer=f"It takes place in {SETTING}.",
        ),
        QAItem(
            question=f"What caused the damage in the reading nook?",
            answer=f"{villain.label} caused the damage when it squeezed into the reading nook and bumped the shelf and rug.",
        ),
        QAItem(
            question=f"How did {hero.label} fix the problem?",
            answer=f"{hero.label} used a magic bookmark and said, 'Magic, mend!' which fixed the damage.",
        ),
        QAItem(
            question=f"How did the story stay funny?",
            answer=f"It stayed funny because {sidekick.label} made a joke about the brontosaurus having superhero-sized tail twirls.",
        ),
        QAItem(
            question=f"What did everyone do at the end?",
            answer=f"At the end, the bookshelf and rug were fixed and everyone curled up to read together in the reading nook.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brontosaurus?",
            answer="A brontosaurus is a very large plant-eating dinosaur with a long neck and a long tail.",
        ),
        QAItem(
            question="What does a magic spell do in stories?",
            answer="In stories, a magic spell can make something change in a surprising way, like fixing a mess or helping a problem.",
        ),
        QAItem(
            question="Why do people use humor in stories?",
            answer="People use humor to make a story feel lighter, funnier, and more enjoyable to hear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world set in a reading nook.")
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
    ap.add_argument("--hero-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--sidekick-type", choices=["cat", "dog", "robot", "bird"], default=None)
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
    hero_name, hero_type = rng.choice(HEROES)
    sidekick_name, sidekick_type = rng.choice(SIDEKICKS)
    villain_name = rng.choice(VILLAINS)

    if args.name:
        hero_name = args.name
    if args.hero_type:
        hero_type = args.hero_type
    if args.sidekick:
        sidekick_name = args.sidekick
    if args.sidekick_type:
        sidekick_type = args.sidekick_type
    if args.villain:
        villain_name = args.villain

    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        villain_name=villain_name,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate()
    world = build_world(params)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams("Mira", "girl", "Bean", "cat", "the wobble-brontosaurus"),
        StoryParams("Toby", "boy", "Pip", "robot", "the giggle-brontosaurus"),
        StoryParams("Nova", "girl", "Dot", "dog", "the sleepy brontosaurus"),
    ]


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show damage/1. #show resolved/0."))
    has_damage = any(sym.name == "damage" for sym in model)
    if has_damage:
        print("OK: ASP model includes damage, matching the Python story gate.")
        return 0
    print("MISMATCH: ASP model did not include damage.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show damage/1. #show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show damage/1. #show resolved/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in curated():
            samples.append(generate(p))
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
