#!/usr/bin/env python3
"""
storyworlds/worlds/piggy_ziti_yorkie_hair_salon_foreshadowing_magic.py
=======================================================================

A small Storyweavers world about a hair salon where a piggy, a ziti bowl,
and a yorkie collide in a tall-tale mood of foreshadowing, magic, and humor.

Premise:
A piggy wants a dramatic new hairstyle at a busy hair salon. A bowl of ziti
keeps appearing before the real trouble starts, and a little yorkie notices
odd magical clues around the mirrors and combs.

Turn:
The salon's magical dryer, foreshadowed by tiny sparks and a singing comb,
starts to tangle the piggy's hair into an impossible knot. The yorkie barks
at the right moment, and the stylist uses a spell hidden in the shampoo foam.

Resolution:
The magic is turned into a playful laugh, the piggy gets a grand new style,
the ziti stays safely on the snack shelf, and the yorkie ends up wearing a
ridiculous ribbon that proves the day changed for good.
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

SALON_TOOLS = ["comb", "brush", "dryer", "spray bottle", "clip"]
MAGIC_SIGNS = ["sparkles", "glimmer", "whisper", "twinkle"]


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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "piggy": {"subject": "it", "object": "it", "possessive": "its"},
            "yorkie": {"subject": "it", "object": "it", "possessive": "its"},
            "stylist": {"subject": "she", "object": "her", "possessive": "her"},
            "child": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Salon:
    name: str = "the hair salon"
    places: set[str] = field(default_factory=lambda: {"hair salon"})
    magic: bool = True


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Piggy"
    salon: str = "hair salon"
    style: str = "tall tale"
    feature1: str = "foreshadowing"
    feature2: str = "magic"
    feature3: str = "humor"


class World:
    def __init__(self, salon: Salon) -> None:
        self.salon = salon
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Hair-salon tall tale about piggy, ziti, and yorkie.")
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
    return StoryParams(seed=args.seed if args.seed is not None else rng.randrange(1 << 30))


def _spark(world: World) -> bool:
    return world.facts.get("foreshadowed", False)


def tell() -> World:
    world = World(Salon())
    piggy = world.add(Entity(id="Piggy", kind="character", type="piggy", label="piggy"))
    yorkie = world.add(Entity(id="Yorkie", kind="character", type="yorkie", label="yorkie"))
    stylist = world.add(Entity(id="Mabel", kind="character", type="stylist", label="Mabel the stylist"))
    ziti = world.add(Entity(id="ziti", type="food", label="ziti", phrase="a warm bowl of ziti", plural=False))
    ribbon = world.add(Entity(id="ribbon", type="thing", label="ribbon", phrase="a bright ribbon"))
    comb = world.add(Entity(id="comb", type="tool", label="comb", phrase="a silver comb"))
    dryer = world.add(Entity(id="dryer", type="tool", label="dryer", phrase="a loud dryer"))

    world.facts.update(piggy=piggy, yorkie=yorkie, stylist=stylist, ziti=ziti, ribbon=ribbon, comb=comb, dryer=dryer)

    world.say("At the hair salon, Piggy arrived with a dream as big as a barn roof and twice as shiny.")
    world.say("Piggy wanted a fancy new style, and Mabel the stylist laughed the kind of laugh that could bounce off three mirrors.")
    world.say("On the front counter sat a warm bowl of ziti, and every time Piggy looked at it, the noodles seemed to grin back.")
    world.say("Yorkie trotted in right behind, tail wagging like a little metronome with a secret.")

    world.para()
    world.say("Before the scissors even snipped, the comb gave a tiny twinkle.")
    world.say("That was the first sign something magical was stirring under the shampoo bubbles.")
    world.say("Yorkie sniffed the air and gave one sharp bark, as if it had read tomorrow's newspaper.")

    world.para()
    world.say("Mabel reached for the dryer, and it puffed up a wind strong enough to ruffle the magazines on the shelf.")
    piggy.memes["hope"] = 1
    piggy.meters["hair"] = 1
    world.say("Piggy held still, trying to look brave, but the dryer kept humming a tune that sounded suspiciously like a marching band in a teacup.")

    if _spark(world):
        piggy.meters["tangle"] = 1
        piggy.memes["alarm"] = 1
        world.say("Then the foreshadowed thing happened: one bright spark leapt from the dryer to Piggy's curls, and the curls tied themselves into one grand knot.")
        world.say("Piggy blinked so hard the mirrors seemed to blink back.")
        world.say("Yorkie barked again, this time so loudly that even the ziti seemed to shiver on the counter.")

    world.para()
    world.say("Mabel did not panic. She smiled, sprinkled a little shampoo foam in the air, and whispered a magic word that sounded like a sneeze with manners.")
    piggy.memes["surprise"] = 1
    piggy.memes["joy"] = 1
    world.say("The foam floated down, the knot loosened, and the tangled curls sprang into a grand, playful style as if they had been waiting for applause.")
    world.say("Then Mabel pinned a bright ribbon near one ear, and Piggy looked proud enough to pose for a parade poster.")

    world.say("Yorkie, being a helpful sort of dog, was given the smallest ribbon tail in the county, and it wagged every time Yorkie twitched.")
    world.say("As for the ziti, it stayed exactly where it belonged, safe and steaming on the counter, which was a mercy for everyone wearing clean clothes.")
    world.say("Piggy left the salon with a magical new haircut, Yorkie strutted beside it, and Mabel declared that even the comb had never seen such a day.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale style story set in a hair salon with piggy, ziti, and yorkie, and include foreshadowing, magic, and humor.',
        'Tell a funny magical story about Piggy getting a new hairstyle while Yorkie notices clues before the surprise happens.',
        'Write a child-friendly salon story where a bowl of ziti, a barking yorkie, and a sparkly comb all matter to the ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Where does the story take place?",
            answer="The story takes place in a hair salon, where mirrors, combs, and a noisy dryer help set the scene.",
        ),
        QAItem(
            question="What was Piggy hoping to get at the salon?",
            answer="Piggy was hoping to get a fancy new hairstyle, and that wish led to the magical trouble and the happy fix.",
        ),
        QAItem(
            question="What clue foreshadowed the magical trouble?",
            answer="The little twinkle from the comb was the clue that something magical was stirring before the dryer caused a knot.",
        ),
        QAItem(
            question="How did Yorkie help?",
            answer="Yorkie helped by barking at the right moments, which warned everyone that the magic was about to do something wild.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The story ended with Piggy wearing a grand new style, Yorkie wearing a tiny ribbon, and the ziti still safely on the counter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a hair salon usually have?",
            answer="A hair salon usually has mirrors, combs, brushes, chairs, and tools for cutting or styling hair.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue early on that something important will happen later.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is when something impossible or surprising happens, like a spell, a sparkle, or a strange change that feels enchanting.",
        ),
        QAItem(
            question="Why can humor make a story fun?",
            answer="Humor can make a story fun because it gives us something silly or surprising to smile about.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "hair_salon"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("feature", "magic"),
            asp.fact("feature", "humor"),
            asp.fact("character", "piggy"),
            asp.fact("character", "yorkie"),
            asp.fact("character", "stylist"),
            asp.fact("object", "ziti"),
            asp.fact("object", "dryer"),
            asp.fact("object", "comb"),
        ]
    )


ASP_RULES = r"""
feature(foreshadowing).
feature(magic).
feature(humor).
story_theme(hair_salon).

compatible_story :- setting(hair_salon), feature(foreshadowing), feature(magic), feature(humor).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/0."))
    ok = any(sym.name == "compatible_story" for sym in model)
    if ok:
        print("OK: ASP reasoner accepts the hair-salon tall tale world.")
        return 0
    print("MISMATCH: ASP reasoner did not derive compatible_story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell()
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


CURATED = [StoryParams(seed=1), StoryParams(seed=2), StoryParams(seed=3)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/0."))
        print("compatible_story" if any(sym.name == "compatible_story" for sym in model) else "no models")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
