#!/usr/bin/env python3
"""
A small fable-like storyworld about sharing a lacrosse set, a tilt of mood,
and a porcupine misunderstanding that turns into a kinder ending.

The seed premise:
- A young porcupine wants to play lacrosse.
- A friend thinks the porcupine is being selfish or mean.
- Suspense builds around a shared game and a tilted basket of gear.
- The misunderstanding is resolved when the friends share the sticks and
  explain the plan.

The world model tracks:
- physical meters: possession, tilt, distance, scratchiness, bruising risk
- emotional memes: trust, worry, misunderstanding, generosity, relief

The prose is fable-like: concrete, short, gentle, and moral-leaning.
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
    plural: bool = False
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["near", "tilt", "possession", "scratch", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["trust", "worry", "misunderstanding", "generosity", "relief", "suspense", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the meadow"
    indoors: bool = False


@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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


PLACES = {
    "meadow": Place("the meadow", False),
    "clearing": Place("the clearing", False),
    "barnyard": Place("the barnyard", False),
    "field": Place("the field", False),
}

NAMES = ["Tilly", "Moss", "Robin", "Pip", "Fern", "Wren"]
PORCUPINE_NAMES = ["Purl", "Quill", "Nettle"]
MOOD_WORDS = ["gentle", "curious", "patient", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like lacrosse storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(place=args.place or rng.choice(list(PLACES)))


def _add_memes(e: Entity, **bits: float) -> None:
    for k, v in bits.items():
        e.memes[k] = e.memes.get(k, 0.0) + v


def _add_meters(e: Entity, **bits: float) -> None:
    for k, v in bits.items():
        e.meters[k] = e.meters.get(k, 0.0) + v


def setup_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type="porcupine", label="porcupine", phrase="a young porcupine"))
    friend = world.add(Entity(id="friend", kind="character", type="rabbit", label="rabbit", phrase="a quick rabbit"))
    elder = world.add(Entity(id="elder", kind="character", type="turtle", label="turtle", phrase="an old turtle"))

    ball = world.add(Entity(id="ball", type="lacrosse ball", label="lacrosse ball", phrase="a soft lacrosse ball"))
    stick1 = world.add(Entity(id="stick1", type="lacrosse stick", label="lacrosse stick", phrase="one lacrosse stick"))
    stick2 = world.add(Entity(id="stick2", type="lacrosse stick", label="lacrosse stick", phrase="another lacrosse stick"))

    world.facts.update(hero=hero, friend=friend, elder=elder, ball=ball, stick1=stick1, stick2=stick2)
    return world


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    elder: Entity = world.facts["elder"]
    ball: Entity = world.facts["ball"]
    stick1: Entity = world.facts["stick1"]
    stick2: Entity = world.facts["stick2"]

    _add_memes(hero, joy=1, generosity=1)
    world.say(f"In {world.place.name}, a young porcupine named {PORCUPINE_NAMES[0]} loved lacrosse.")
    world.say(f"{PORCUPINE_NAMES[0]} was {random.choice(MOOD_WORDS)} and always looked for a way to share the game.")
    world.say(f"A quick rabbit named {NAMES[0]} watched from the grass, and an old turtle sat nearby with wise eyes.")
    world.say(f"They had one soft lacrosse ball and two sticks, but one basket on the fence had been tilted by the wind.")

    world.para()
    _add_meters(stick1, possession=1)
    _add_memes(hero, suspense=1)
    world.say(f"{PORCUPINE_NAMES[0]} picked up one stick and carried the ball to the middle of the field.")
    world.say(f"The rabbit thought the porcupine meant to keep the other stick for itself.")
    _add_memes(friend, worry=1, misunderstanding=1)
    _add_memes(hero, worry=0.5)

    world.say(f"“Wait,” said the rabbit. “Why are you taking the best stick and leaving me the small one?”")
    _add_meters(world.get("stick2"), tilt=1)
    world.say(f"The tilted basket wobbled in the breeze, and the rabbit's ears went still with suspense.")

    world.para()
    _add_memes(elder, trust=1)
    world.say(f"The old turtle smiled and said, “A thing can look greedy when a plan is still half-hidden.”")
    world.say(f"{PORCUPINE_NAMES[0]} set the ball down and pointed to the tilted basket.")
    world.say(f"“I was only moving the sticks so we could share them fairly,” said the porcupine.")
    _add_memes(hero, generosity=1)
    _add_memes(friend, misunderstanding=-1, worry=-1, trust=1)

    world.say(f"The rabbit blinked, then saw the second stick waiting all along.")
    world.say(f"The porcupine gave one stick to the rabbit and kept one for itself.")
    _add_meters(stick1, possession=0)
    _add_meters(stick2, possession=0)
    stick1.owner = "hero"
    stick2.owner = "friend"
    _add_memes(hero, relief=1, joy=1)
    _add_memes(friend, relief=1, joy=1)

    world.para()
    world.say(f"Together they repaired the tilted basket, then played a careful game of lacrosse in the meadow.")
    world.say(f"The rabbit learned that a quiet delay is not always a selfish act.")
    world.say(f"The porcupine learned that a clear explanation can be kinder than a hurried guess.")
    world.say(f"And the old turtle nodded, because shared things grow better when friends speak plainly.")

    world.facts.update(
        place=params.place,
        hero_name=PORCUPINE_NAMES[0],
        friend_name=NAMES[0],
        setting_name=world.place.name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short fable about lacrosse, sharing, and a misunderstanding caused by a tilted basket.",
        "Tell a gentle animal story where a porcupine and a rabbit learn to share a lacrosse set.",
        "Write a child-friendly fable with suspense that ends in a fair and friendly game of lacrosse.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero_name"]
    friend = world.facts["friend_name"]
    return [
        QAItem(
            question=f"Why did the rabbit worry when {hero} carried the lacrosse stick?",
            answer="The rabbit thought the porcupine was keeping the best stick and being unfair, but that was a misunderstanding."
        ),
        QAItem(
            question="What made the moment feel suspenseful?",
            answer="The tilted basket wobbled in the breeze, so no one knew right away whether the sticks were being hidden or shared."
        ),
        QAItem(
            question="What changed the misunderstanding at the end?",
            answer=f"{hero} explained the plan, gave one stick to the rabbit, and the two friends saw that they were meant to share."
        ),
        QAItem(
            question=f"How did {friend} feel after the explanation?",
            answer="The rabbit felt relieved and happy, because the porcupine had been planning a fair game all along."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lacrosse?",
            answer="Lacrosse is a game where players use long sticks with netted heads to catch, carry, and move a ball."
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use, hold, or enjoy something too."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone guesses the wrong meaning before the real plan is explained."
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to find out what will happen next."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}={v:.1f}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v:.1f}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_place/1.
valid_place(meadow) :- true.
valid_place(clearing) :- true.
valid_place(barnyard) :- true.
valid_place(field) :- true.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", p) for p in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    found = sorted(set(asp.atoms(model, "valid_place")))
    wanted = sorted((p,) for p in PLACES)
    if found == wanted:
        print(f"OK: ASP matches Python ({len(found)} places).")
        return 0
    print("MISMATCH")
    print("asp:", found)
    print("py:", wanted)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="meadow"),
    StoryParams(place="clearing"),
    StoryParams(place="field"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_place/1."))
        print("\n".join(str(t) for t in sorted(set(asp.atoms(model, "valid_place")))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if args.all:
            header = f"### {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
