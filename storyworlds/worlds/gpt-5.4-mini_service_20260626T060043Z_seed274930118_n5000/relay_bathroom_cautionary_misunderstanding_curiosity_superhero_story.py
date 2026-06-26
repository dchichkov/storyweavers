#!/usr/bin/env python3
"""
A small storyworld about a curious little superhero in a bathroom, a relay
object, a cautionary warning, and a misunderstanding that gets resolved.
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

HERO_NAMES = ["Milo", "Nia", "Tessa", "Rory", "Lina", "Jasper"]
SIDEKICK_NAMES = ["Dot", "Pip", "Zara", "Arlo", "Bree", "Finn"]
VILLAIN_NAMES = ["Drip", "Mirth", "Murmur", "Slink"]
GADGETS = ["cape", "mask", "gloves", "boots"]
WARNING_WORDS = ["careful", "watch out", "be gentle", "hold on"]
MISUNDERSTANDINGS = [
    "thought the relay was a race to the sink",
    "thought the relay was a word for a shiny baton",
    "thought the relay should be tossed into the tub",
    "thought the relay meant they had to hurry through everything",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    sidekick: str
    villain: str
    gadget: str
    warning: str
    misunderstanding: str
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


def build_story(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    sidekick = w.add(Entity(id=params.sidekick, kind="character", type="boy", label=params.sidekick))
    villain = w.add(Entity(id=params.villain, kind="character", type="thing", label=params.villain))
    relay = w.add(Entity(id="relay", type="relay", label="relay", phrase="a silver relay baton"))
    gadget = w.add(Entity(id=params.gadget, type="gear", label=params.gadget, phrase=f"a bright {params.gadget}"))

    hero.memes["curiosity"] = 1
    sidekick.memes["curiosity"] = 1
    hero.meters["bravery"] = 1
    relay.meters["shine"] = 1

    w.say(
        f"{hero.id} was a tiny superhero with a bright {params.gadget} and a big curious heart."
    )
    w.say(
        f"On the bathroom shelf, {hero.id} found {relay.phrase}, and {hero.pronoun()} wanted to know what it was for."
    )
    w.say(
        f"{sidekick.id} said {params.warning}, but {hero.id} was busy peeking at every button and bottle."
    )

    w.para()
    hero.memes["curiosity"] += 1
    w.say(
        f"{hero.id} {params.misunderstanding}, so {hero.pronoun()} lifted the relay as if it were a special mission tool."
    )
    w.say(
        f"That made {villain.id} the splashy troublemaker grin, because a wrong guess could turn the bathroom into a slippery mess."
    )

    w.para()
    hero.memes["worry"] = 1
    sidekick.memes["worry"] = 1
    w.say(
        f"Then {sidekick.id} pointed at the towel hook and explained that the relay was for passing a job along, not for tossing or racing."
    )
    w.say(
        f"{hero.id} blinked, looked at the smooth floor, and understood the cautionary warning at once."
    )
    w.say(
        f"Together they carried the relay carefully, set it by the sink, and used the {params.gadget} to help clean the tiny splash."
    )

    w.para()
    hero.memes["joy"] = 2
    hero.memes["curiosity"] = 0
    w.say(
        f"After that, {hero.id} smiled like a true hero: curious, but careful, with the relay safe and the bathroom calm again."
    )

    w.facts.update(hero=hero, sidekick=sidekick, villain=villain, relay=relay, gadget=gadget, params=params)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a superhero story in a bathroom that includes a relay and shows what happens when {p.name} is curious.',
        f"Tell a gentle cautionary story where {p.name} and {p.sidekick} misunderstand a relay and then fix the mistake.",
        "Write a short, child-friendly superhero story with a bathroom, a warning, a misunderstanding, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero = f["hero"]
    sidekick = f["sidekick"]
    return [
        QAItem(
            question=f"Who is the superhero in the bathroom story?",
            answer=f"The superhero is {p.name}, who is curious, brave, and wearing a {p.gadget}.",
        ),
        QAItem(
            question=f"What did {p.name} misunderstand about the relay?",
            answer=f"{p.name} {p.misunderstanding}, which was the wrong idea.",
        ),
        QAItem(
            question=f"How did {p.sidekick} help after the warning?",
            answer=f"{p.sidekick} explained what the relay was really for, so {p.name} could be careful instead of making a mess.",
        ),
        QAItem(
            question=f"How did the story end for {p.name}?",
            answer=f"At the end, {p.name} felt proud, the relay stayed safe, and the bathroom was calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a relay?",
            answer="A relay is something passed from one person to another, or a system that helps something continue in order.",
        ),
        QAItem(
            question="Why should people be careful in a bathroom?",
            answer="Bathrooms can have wet floors and slippery spots, so being careful helps people avoid accidents.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more and asking questions about something new or interesting.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "bathroom"),
        asp.fact("trait", "cautionary"),
        asp.fact("trait", "misunderstanding"),
        asp.fact("trait", "curiosity"),
        asp.fact("object", "relay"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
trait_story(bathroom) :- place(bathroom), trait(cautionary), trait(misunderstanding), trait(curiosity).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show trait_story/1."))
    ok = bool(asp.atoms(model, "trait_story"))
    if ok:
        print("OK: ASP reasonableness gate is present.")
        return 0
    print("MISMATCH: ASP reasonableness gate failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld set in a bathroom.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--villain", choices=VILLAIN_NAMES)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--warning", choices=WARNING_WORDS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
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
    return StoryParams(
        name=args.name or rng.choice(HERO_NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICK_NAMES),
        villain=args.villain or rng.choice(VILLAIN_NAMES),
        gadget=args.gadget or rng.choice(GADGETS),
        warning=args.warning or rng.choice(WARNING_WORDS),
        misunderstanding=args.misunderstanding or rng.choice(MISUNDERSTANDINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show trait_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show trait_story/1."))
        print(asp.atoms(model, "trait_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = [
            StoryParams("Milo", "Dot", "Drip", "cape", "careful", MISUNDERSTANDINGS[0]),
            StoryParams("Nia", "Pip", "Mirth", "mask", "watch out", MISUNDERSTANDINGS[1]),
            StoryParams("Tessa", "Zara", "Murmur", "gloves", "be gentle", MISUNDERSTANDINGS[2]),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
