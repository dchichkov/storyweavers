#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a lioness who learns bravery through dialogue
and earns reconciliation after a small misunderstanding in the pride's valley.
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
    kind: str = "character"
    type: str = "being"
    name: str = ""
    title: str = ""
    role: str = ""
    gender: str = "female"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return "she" if self.gender == "female" else "he"
        if case == "object":
            return "her" if self.gender == "female" else "him"
        return "her" if self.gender == "female" else "his"

    def label(self) -> str:
        return self.title or self.name or self.type


@dataclass
class Place:
    id: str
    name: str
    mood: str
    light: str
    secret: str


@dataclass
class StoryParams:
    place: str = "sunny_glade"
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

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


PLACES = {
    "sunny_glade": Place(
        id="sunny_glade",
        name="the sunny glade",
        mood="bright",
        light="golden",
        secret="a narrow trail behind the elder stones",
    ),
    "moon_pond": Place(
        id="moon_pond",
        name="the moon pond",
        mood="quiet",
        light="silver",
        secret="a fern arch near the reeds",
    ),
    "rose_hollow": Place(
        id="rose_hollow",
        name="the rose hollow",
        mood="gentle",
        light="pink",
        secret="a little bridge over the brook",
    ),
}


ASP_RULES = r"""
place(sunny_glade). place(moon_pond). place(rose_hollow).
mood(sunny_glade, bright). mood(moon_pond, quiet). mood(rose_hollow, gentle).
scene(P) :- place(P), mood(P, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("mood", pid, p.mood))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def brave_lioness(world: World) -> Entity:
    lioness = world.add(Entity(
        id="Luna",
        kind="character",
        type="lioness",
        name="Luna",
        title="the lioness",
        role="young protector",
        gender="female",
    ))
    lioness.meters["courage"] = 0.0
    lioness.meters["distance"] = 0.0
    lioness.memes["worry"] = 0.0
    lioness.memes["hope"] = 0.0
    lioness.memes["hurt"] = 0.0
    lioness.memes["love"] = 1.0
    return lioness


def elder(world: World) -> Entity:
    keeper = world.add(Entity(
        id="Mara",
        kind="character",
        type="lioness",
        name="Mara",
        title="the elder lioness",
        role="keeper of the glade",
        gender="female",
    ))
    keeper.meters["age"] = 1.0
    keeper.memes["care"] = 1.0
    keeper.memes["worry"] = 0.0
    return keeper


def bird(world: World) -> Entity:
    sparrow = world.add(Entity(
        id="Pip",
        kind="character",
        type="bird",
        name="Pip",
        title="the little bird",
        role="messenger",
        gender="female",
    ))
    sparrow.memes["fear"] = 0.0
    sparrow.memes["trust"] = 0.0
    return sparrow


def tell(place: Place) -> World:
    world = World(place=place)
    luna = brave_lioness(world)
    mara = elder(world)
    pip = bird(world)

    world.say(f"Long ago, in {place.name}, there lived {luna.title} named Luna.")
    world.say(
        f"{luna.pronoun().capitalize()} loved the warm grass and the golden light, "
        f"and {luna.pronoun('subject')} wished to be brave enough to help others."
    )
    world.say(
        f"Near the old stones, {pip.title} often sang, and {mara.title} watched the paths "
        f"with wise, calm eyes."
    )

    world.para()
    world.say(
        f"One evening, a wind slid through the glade and frightened Pip into the high reeds."
    )
    luna.memes["worry"] += 1
    pip.memes["fear"] += 1
    world.say(
        f"Luna saw the trembling wings and stepped forward, though her paws felt small at first."
    )
    luna.meters["distance"] += 1
    luna.meters["courage"] += 1
    world.say(
        f"She took one brave step, then another, because a kind heart can be bolder than fear."
    )

    world.para()
    world.say(
        f"Luna called softly, 'Pip, I am here. You are safe.'"
    )
    world.say(
        f"Pip fluttered and answered, 'I was afraid of the dark reeds. Will you help me?'"
    )
    world.say(
        f"Luna listened and replied, 'Yes. We will walk together, and I will not leave you alone.'"
    )
    pip.memes["trust"] += 1
    luna.memes["hope"] += 1

    world.para()
    world.say(
        f"But when Luna pushed through the reeds, she brushed the old nest by mistake, "
        f"and Pip cried out in hurt surprise."
    )
    luna.memes["hurt"] += 1
    mara.memes["worry"] += 1
    world.say(
        f"The elder lioness came at once and said, 'A brave paw must also be a careful paw.'"
    )
    world.say(
        f"Luna bowed her head and answered, 'I meant to help, not to harm.'"
    )
    world.say(
        f"Mara asked, 'Will you speak plainly, and will you listen plainly too?'"
    )
    world.say(
        f"Luna said, 'Yes.' Pip said, 'Yes.' And the three of them stood together in the soft grass."
    )

    world.para()
    world.say(
        f"Luna looked at Pip and spoke with a gentle voice: 'I am sorry I startled you.'"
    )
    world.say(
        f"Pip blinked, then said, 'And I am sorry I hid without calling back.'"
    )
    world.say(
        f"Mara smiled, because true reconciliation grows when two voices meet with honesty."
    )
    world.say(
        f"Together they mended the nest, and Luna carried the broken reeds with careful paws."
    )
    world.say(
        f"When the moon rose above {place.name}, Pip sang again, Luna stood proudly beside the stones, "
        f"and the glade felt peaceful and new."
    )

    world.facts.update(
        place=place,
        luna=luna,
        mara=mara,
        pip=pip,
        brave_step=True,
        apology=True,
        reconciliation=True,
        dialogue=True,
        hurt=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"].name
    return [
        f"Write a fairy tale about a lioness in {place} who shows bravery by speaking kindly.",
        f"Tell a short story where a lioness helps a frightened friend and later makes peace after a mistake.",
        f"Write a child-friendly fairy tale with dialogue, bravery, and reconciliation in {place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    luna: Entity = world.facts["luna"]
    mara: Entity = world.facts["mara"]
    pip: Entity = world.facts["pip"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question="Who is the main character in the story?",
            answer=f"The main character is Luna, a young lioness who lives in {place.name}.",
        ),
        QAItem(
            question="What made Luna brave?",
            answer="Luna was brave because she stepped toward Pip even though the wind and dark reeds made her nervous.",
        ),
        QAItem(
            question="Why did Luna and Pip need reconciliation?",
            answer="They needed reconciliation because Luna accidentally brushed Pip's nest, and then they talked, apologized, and mended the nest together.",
        ),
        QAItem(
            question="What kind of words helped solve the problem?",
            answer="Gentle dialogue helped solve the problem, because Luna, Pip, and Mara spoke honestly and listened to one another.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lioness?",
            answer="A lioness is a female lion. Lionesses are strong animals and often care for their pride and young cubs.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary when it matters, even if your paws shake a little.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or hurt feeling.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is a conversation where people speak and listen to each other so they can understand one another better.",
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
    lines = [f"place={world.place.id}"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type}, meters={dict(e.meters)}, memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: a lioness, bravery, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
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
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place])
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show scene/1."))
    scenes = sorted(set(asp.atoms(model, "scene")))
    python_scenes = sorted((pid,) for pid in PLACES)
    if scenes == python_scenes:
        print("OK: ASP and Python agree on the scene inventory.")
        return 0
    print("Mismatch between ASP and Python scene inventory.")
    print("ASP:", scenes)
    print("Python:", python_scenes)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show scene/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(sorted(PLACES)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place_id in PLACES:
            params = StoryParams(place=place_id, seed=base_seed)
            samples.append(generate(params))
    else:
        rng = random.Random(base_seed)
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
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
            print(f"### story {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
