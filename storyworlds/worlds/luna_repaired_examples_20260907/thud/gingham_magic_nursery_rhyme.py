#!/usr/bin/env python3
"""
A tiny Storyweavers world about a gingham blanket, a little bit of magic,
and a nursery-rhyme rescue.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Arc:
    key: str
    object_name: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    magic: tuple[str, str]
    ending: tuple[str, str]
    problem: str
    action: str
    result: str


ARCS = (
    Arc(
        "moon_pocket",
        "blanket",
        (
            "In the nursery, Nora spread a gingham blanket bright,",
            "It held her wooden moon and made the pillows right.",
        ),
        (
            "But moon and blanket floated up and bumped the ceiling blue.",
            "The moon was stuck above the bed, and Nora did not know what to do.",
        ),
        (
            "She tapped three stars upon the cloth and whispered, \"Down, moon, down!\"",
            "The gingham checks began to glow and twirled the moon around.",
        ),
        (
            "The moon came softly to her hand and shone beside her head.",
            "The gingham blanket tucked her in: \"Good-night,\" the moonlight said.",
        ),
        "the toy moon rose away with the gingham blanket",
        "Nora tapped three stars and spoke a gentle rhyme",
        "the magic brought the moon safely back",
    ),
    Arc(
        "runaway_ribbon",
        "ribbon",
        (
            "By the cradle lay a gingham bow, all rosy, white, and neat,",
            "Pip tied it to a magic bell with tiny silver feet.",
        ),
        (
            "The ribbon zipped around the room and tugged the curtain wide.",
            "The sleepy toys began to chase; there was no place to hide.",
        ),
        (
            "Pip clapped twice and sang a rhyme, \"Be still, you flying thread!\"",
            "The gingham checks blinked one by one, and round the ribbon sped.",
        ),
        (
            "The ribbon curled beside the bell and rested in a bow.",
            "The toys climbed back into their bed, while soft moon shadows glowed.",
        ),
        "a magic ribbon raced around the nursery",
        "Pip used a clap and a rhyming spell",
        "the ribbon curled safely beside the bell",
    ),
    Arc(
        "starry_quilt",
        "quilt",
        (
            "A gingham quilt lay on the chair, with squares of green and red,",
            "Mia placed a paper star upon its little bed.",
        ),
        (
            "The star slipped through a shining seam and twinkled in the hall.",
            "It lit the toys and woke the socks, then made the slippers dance and call.",
        ),
        (
            "Mia stitched one silver button on and sang a counting tune.",
            "The gingham squares made stepping-stones that led the star back soon.",
        ),
        (
            "The paper star returned to rest beneath the quilt's warm fold.",
            "The nursery grew quiet again, while every square shone gold.",
        ),
        "a paper star slipped through the quilt and woke the nursery",
        "Mia stitched a silver button and sang a counting tune",
        "the magic path guided the star back under the quilt",
    ),
    Arc(
        "pocket_sprites",
        "apron",
        (
            "Tom wore a gingham apron while he set the cups in rows,",
            "A little pocket jingled with three buttons and a rose.",
        ),
        (
            "The buttons bounced like tiny sprites and skipped beneath the chair.",
            "Tom searched beside the blocks, but found no buttons there.",
        ),
        (
            "He rhymed, \"By square and stripe, return tonight!\" and spun around once more.",
            "The gingham pocket gave a puff; three buttons rolled across the floor.",
        ),
        (
            "Tom buttoned up his apron and poured warm pretend tea.",
            "The sprites became still buttons, snug as snug buttons could be.",
        ),
        "three magic buttons escaped from a gingham pocket",
        "Tom spoke a rhyme about squares and stripes",
        "the buttons returned and stayed in the pocket",
    ),
)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str = "girl"
    seed: Optional[int] = None


PLACES = {
    "nursery": Place("nursery", "the moonlit nursery", {"room", "sleepy"}),
    "playroom": Place("playroom", "the sunny playroom", {"room", "bright"}),
    "cottage": Place("cottage", "the little cottage room", {"home", "warm"}),
}

NAMES = {
    "girl": ["Nora", "Mia", "Lily", "Ava"],
    "boy": ["Pip", "Tom", "Leo", "Sam"],
}

CURATED = [
    StoryParams("nursery", "Nora", "girl"),
    StoryParams("playroom", "Pip", "boy"),
    StoryParams("cottage", "Mia", "girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(args.place or rng.choice(list(PLACES)), name, gender)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.child_gender not in NAMES:
        raise StoryError(f"Unknown child gender: {params.child_gender}.")
    if not params.child_name.strip():
        raise StoryError("The child must have a name.")

    world = World(PLACES[params.place])
    child = world.add(Entity(params.child_name, "character", params.child_gender, params.child_name))
    gingham = world.add(Entity("gingham", "thing", "cloth", "gingham cloth"))
    magic = world.add(Entity("magic", "force", "magic", "gentle magic"))

    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.child_name)))
    arc = ARCS[rng.randrange(len(ARCS))]
    object_entity = world.add(Entity("wonder", "thing", "nursery_object", arc.object_name))

    values = {"name": params.child_name}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    child.meters["trouble"] = 1.0
    child.memes["worry"] = 1.0
    object_entity.meters["adrift"] = 1.0
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    child.meters["spell_spoken"] = 1.0
    child.memes["bravery"] = 1.0
    magic.meters["awake"] = 1.0
    gingham.memes["glowing"] = 1.0
    for line in arc.magic:
        world.say(line.format(**values))
    world.para()

    object_entity.meters["safe"] = 1.0
    object_entity.meters["adrift"] = 0.0
    child.memes["joy"] = 1.0
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        child=child,
        object=object_entity,
        gingham=gingham,
        magic=magic,
        place=world.place,
        arc=arc.key,
        problem=arc.problem,
        action=arc.action,
        result=arc.result,
        final_image=arc.ending[1].format(**values),
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle nursery rhyme containing the word "gingham" and a little magic.',
        f"Tell a child-friendly story in {f['place'].label} where {f['problem']}.",
        f"Show how {f['child'].id} uses a rhyme and magic so that {f['result']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What went wrong in the nursery?",
            f"In {f['place'].label}, {f['problem']}. The unusual trouble made the child pause and think.",
        ),
        QAItem(
            "How was the problem solved?",
            f"{f['child'].id} solved it by {f['action']}. The gentle gingham magic worked, so {f['result']}.",
        ),
        QAItem(
            "What showed that everything was safe at the end?",
            f"The ending image showed the change: {f['final_image']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven cloth with a simple checked pattern, often made with two cheerful colors.",
        ),
        QAItem(
            "What is magic in a nursery rhyme?",
            "Magic in a nursery rhyme is an imagined wonder that helps a character solve a gentle problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={dict(meters)}")
        if memes:
            details.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:10} ({entity.type:12}) {' '.join(details)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe(wonder) :- spell_spoken(child), magic_awake(magic), adrift(wonder).
solved :- safe(wonder).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child", "child"),
            asp.fact("gingham", "gingham"),
            asp.fact("magic", "magic"),
            asp.fact("wonder", "wonder"),
            asp.fact("spell_spoken", "child"),
            asp.fact("magic_awake", "magic"),
            asp.fact("adrift", "wonder"),
        ]
    )


def asp_program(show: str = "#show solved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not any(sym.name == "solved" for sym in model):
            print("ASP parity failed: solved was not derived.")
            return 1
        sample = generate(StoryParams("nursery", "Nora", "girl", 7))
        if not sample.story.strip() or not sample.world.facts["solved"]:
            print("Story generation failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: ASP and Python smoke tests passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gingham magic nursery-rhyme storyworld.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/0."))
        print([str(symbol) for symbol in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
