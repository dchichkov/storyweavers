#!/usr/bin/env python3
"""
A small magical nursery-rhyme storyworld about gingham in a moonlit nursery.

A child discovers that a gingham blanket has lost its rhyme-magic. With help
from a moon mouse, the child follows a thread of silver stitches, repairs the
blanket, and restores a gentle bedtime song.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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


@dataclass
class StoryParams:
    child_name: str
    mouse_name: str
    charm_id: Optional[str] = None
    verse_id: Optional[str] = None
    seed: Optional[int] = None


CHILDREN = ["Mina", "Pip", "Nell", "Toby", "Rose", "Kit"]
MICE = ["Mallow", "Moonbeam", "Pipkin", "Clover", "Button"]
CHARMS = ["silver_thimble", "blue_button", "starry_bell", "pearl_pin"]
VERSES = ["moon_bed", "little_lamb", "gingham_song", "sleepy_train"]


@dataclass(frozen=True)
class Charm:
    id: str
    name: str
    sign: str
    power: str
    repair: str


@dataclass(frozen=True)
class Verse:
    id: str
    opening: str
    middle: str
    ending: str
    lesson: str


CHARM_REGISTRY = [
    Charm(
        "silver_thimble",
        "a silver thimble",
        "a bright dimple in the blue checks",
        "needle-fine moonlight",
        "a careful stitch around the torn corner",
    ),
    Charm(
        "blue_button",
        "a blue button",
        "a round blue moon among the checks",
        "a tiny turning spell",
        "a neat blue loop through the loose thread",
    ),
    Charm(
        "starry_bell",
        "a starry bell",
        "a soft gold jingle beneath the pillow",
        "a ringing beam of starlight",
        "three quiet knots beside the bell",
    ),
    Charm(
        "pearl_pin",
        "a pearl pin",
        "a pearl gleaming in the gingham border",
        "a warm pearl glow",
        "a smooth crossing stitch in the border",
    ),
]

VERSE_REGISTRY = [
    Verse(
        "moon_bed",
        "Hush-a-bye, checks of white and blue,",
        "Moon-mouse brings a thread to you;",
        "Stitch by stitch the night grows bright,",
        "small brave hands can mend the light.",
    ),
    Verse(
        "little_lamb",
        "Little lamb in gingham gray,",
        "lost your sleepy tune today;",
        "Find the thread and tie it tight,",
        "kindness brings the song back right.",
    ),
    Verse(
        "gingham_song",
        "Gingham squares go row by row,",
        "where the silver night winds blow;",
        "When two friends share what they know,",
        "even quiet magic grows.",
    ),
    Verse(
        "sleepy_train",
        "Clickety-clack, the dream train came,",
        "but one loose thread forgot its name;",
        "Pull it through and softly sing,",
        "care can mend most anything.",
    ),
]

CHARM_BY_ID = {c.id: c for c in CHARM_REGISTRY}
VERSE_BY_ID = {v.id: v for v in VERSE_REGISTRY}


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0x61A9)
    text = "|".join([params.child_name, params.mouse_name, params.charm_id or "", params.verse_id or ""])
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(text)))


def _choose(params: StoryParams) -> tuple[Charm, Verse]:
    rng = _rng(params)
    charm = CHARM_BY_ID.get(params.charm_id or "")
    verse = VERSE_BY_ID.get(params.verse_id or "")
    if charm is None:
        charm = rng.choice(CHARM_REGISTRY)
    if verse is None:
        verse = rng.choice(VERSE_REGISTRY)
    return charm, verse


def build_world(params: StoryParams) -> World:
    charm, verse = _choose(params)
    rng = _rng(params)
    world = World("the moonlit nursery")

    child = world.add(Entity("child", "character", params.child_name))
    mouse = world.add(Entity("mouse", "character", params.mouse_name))
    blanket = world.add(Entity("blanket", "thing", "the gingham blanket"))
    charm_entity = world.add(Entity("charm", "thing", charm.name))
    moon = world.add(Entity("moon", "thing", "the round moon"))

    blanket.meters.update(rhyme=0.0, warmth=1.0, tear=1.0)
    child.memes.update(courage=1.0, care=0.0, wonder=1.0)
    mouse.memes.update(helpfulness=1.0, trust=1.0)
    moon.meters["light"] = 2.0

    openings = [
        f"In the moonlit nursery, {params.child_name} found a gingham blanket folded on the little bed.",
        f"At bedtime, {params.child_name} heard a whisper beneath the gingham blanket.",
        f"By the window, where moonbeams made silver squares, {params.child_name} saw the gingham blanket tremble.",
    ]
    world.say(rng.choice(openings))
    world.say(f"Its white-and-blue checks were still bright, but its bedtime rhyme had vanished from the air.")
    world.say(f"The blanket's corner was loose, and {charm.sign} showed where the missing magic had slipped away.")

    world.para()
    child.memes["courage"] += 1.0
    mouse.memes["helpfulness"] += 1.0
    world.say(f'"Do not fret," whispered {params.mouse_name}, a moon mouse no bigger than a mitten.')
    world.say(f'"We will follow the silver thread, for every lost rhyme leaves a tiny trail."')
    world.say(
        f"Together they looked beneath the pillow, behind the toy chest, and around the cradle. "
        f"At last, the trail curled toward {charm.name}."
    )
    world.say(f"The charm held {charm.power}, but the gingham magic was too weak to wake it.")

    world.para()
    child.memes["care"] += 1.0
    mouse.memes["trust"] += 1.0
    world.say(f"{params.child_name} did not tug or tear. Instead, {params.child_name} held the cloth gently while {params.mouse_name} guided the thread.")
    world.say(f"They used {charm.name} and made {charm.repair}.")
    world.say(f"Then {params.child_name} spoke the first line: “{verse.opening}”")
    world.say(f"{params.mouse_name} answered, “{verse.middle}”")
    blanket.meters["tear"] = 0.0
    blanket.meters["rhyme"] = 1.0
    blanket.meters["warmth"] = 2.0
    world.say(f"The checks shimmered. {verse.ending}")

    world.para()
    child.memes["care"] += 1.0
    child.memes["relief"] = 1.0
    mouse.memes["relief"] = 1.0
    world.say(f"The nursery filled with a soft, steady song, and the blanket grew warm around the sleepy bed.")
    world.say(f"{params.child_name} thanked {params.mouse_name}, then tucked the moon mouse beside the pillow.")
    world.say(f"Together they finished the verse: “{verse.lesson}”")
    world.say(f"The moon shone through the gingham squares, and every square held one small star of restored magic.")

    world.facts.update(
        child=child,
        mouse=mouse,
        blanket=blanket,
        charm=charm,
        charm_entity=charm_entity,
        moon=moon,
        verse=verse,
        place=world.place,
        repaired=True,
        rhyme_restored=True,
        ending="the moon shone through the gingham squares, and every square held one small star of restored magic",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly nursery rhyme story in {f['place']} about {f['child'].label} and {f['mouse'].label}.",
        f"Include a magical gingham blanket whose rhyme has vanished, then show the friends following a thread to {f['charm'].name}.",
        f"Use the verse idea “{f['verse'].opening} {f['verse'].middle}” and end with the repaired blanket glowing under moonlight.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    mouse = f["mouse"].label
    charm = f["charm"]
    return [
        QAItem(
            f"What was wrong with the gingham blanket?",
            f"The gingham blanket had lost its bedtime rhyme because a corner was loose and its magic had slipped away.",
        ),
        QAItem(
            f"Who helped {child} find the missing magic?",
            f"{mouse} helped {child} follow the silver thread to {charm.name}.",
        ),
        QAItem(
            f"How did the friends repair the blanket?",
            f"They held the cloth gently, used {charm.name}, and made {charm.repair}. Then they spoke the nursery verse together.",
        ),
        QAItem(
            "What happened when the rhyme returned?",
            "The gingham checks shimmered, the nursery filled with a soft song, and the blanket grew warm around the bed.",
        ),
        QAItem(
            "What proved that the magic was restored?",
            "Moonlight shone through the gingham squares, and every square held one small star of restored magic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is gingham?", "Gingham is a woven cloth with a checked pattern, often made from two colors."),
        QAItem("What is magic?", "Magic is an imagined power that can make extraordinary things happen in a story."),
        QAItem("What is a nursery rhyme?", "A nursery rhyme is a short, playful poem or song for children."),
        QAItem("Why should cloth be handled gently?", "Cloth lasts longer when it is handled gently, especially when a thread or seam is loose."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.label}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"  place: {world.place}")
    lines.append(f"  repaired: {world.facts.get('repaired')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "nursery"),
            asp.fact("material", "gingham"),
            asp.fact("feature", "magic"),
            asp.fact("style", "nursery_rhyme"),
            asp.fact("action", "follow_thread"),
            asp.fact("action", "repair"),
            asp.fact("action", "sing"),
            asp.fact("state", "lost_rhyme"),
            asp.fact("goal", "restore_rhyme"),
        ]
    )


ASP_RULES = r"""
thread_found :- action(follow_thread), material(gingham).
blanket_repaired :- action(repair), thread_found.
rhyme_restored :- blanket_repaired, action(sing), feature(magic).
valid_story :- setting(nursery), style(nursery_rhyme), rhyme_restored.
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm the magical nursery story.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("rhyme_restored"):
            print("MISMATCH: generated story did not restore the rhyme.")
            return 1
    print("OK: ASP twin and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magical gingham nursery-rhyme storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--mouse")
    parser.add_argument("--charm", choices=CHARMS)
    parser.add_argument("--verse", choices=VERSES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        child_name=args.name or rng.choice(CHILDREN),
        mouse_name=args.mouse or rng.choice(MICE),
        charm_id=args.charm or rng.choice(CHARMS),
        verse_id=args.verse or rng.choice(VERSES),
    )


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams("Mina", "Mallow", "silver_thimble", "moon_bed"),
    StoryParams("Pip", "Button", "blue_button", "gingham_song"),
    StoryParams("Rose", "Moonbeam", "starry_bell", "sleepy_train"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
