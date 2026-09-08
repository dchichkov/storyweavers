#!/usr/bin/env python3
"""
A small cautionary detective storyworld about a library, havoc, and magic.

Luna investigates a magical transformation that has thrown the library into
havoc. The solution depends on observing clues, listening to a witness, and
using a careful rule rather than a flashy spell.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


METERS = {"disorder", "danger", "clues", "calm", "trust"}
MEMES = {"worry", "curiosity", "courage", "patience", "relief"}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class LibraryWorld:
    name: str
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    shelves: dict[str, str] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METERS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEMES})


@dataclass
class StoryParams:
    hero_name: str
    librarian_name: str
    library_name: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Sol"]
LIBRARIAN_NAMES = ["Ms. Bell", "Mr. Reed", "Ada Quill", "Mara Page"]
LIBRARY_NAMES = ["Moonbeam Library", "The Lantern Library", "Maple Street Library", "The Quiet Library"]
PLACES = ["the town square", "Willow Lane", "the old market", "the hilltop"]
AWARDS = ["a silver bookmark", "the library key", "a brass reading lamp", "a detective badge"]

SCENES = [
    {
        "id": "feathers",
        "object": "the history books",
        "transformation": "the history books had changed into fluttering paper birds",
        "omen": "a single blue feather lay beside the locked spell cabinet",
        "danger": "the paper birds were carrying pages toward the open chimney",
        "clue": "each bird had a tiny ink mark shaped like a crescent",
        "method": "followed the crescent marks to the spell cabinet",
        "complication": "a gust scattered the birds across the reading room",
        "turn": "closed the windows and used the quiet bell to guide the birds back",
        "resolution": "the history books settled onto their shelf with every page restored",
        "ending": "a blue feather rested inside the proper history book",
    },
    {
        "id": "sleeping_books",
        "object": "the adventure books",
        "transformation": "the adventure books had become snoring pillows",
        "omen": "a warm trail of golden dust led from the shelf to the forbidden magic desk",
        "danger": "the pillows would erase their stories if the dust reached the desk lamp",
        "clue": "the dust glittered only when someone said the word 'hurry'",
        "method": "watched the glitter without saying the dangerous word",
        "complication": "the librarian shouted when a stack toppled near the desk",
        "turn": "raised a hand for silence and slid a rug beneath the wobbling stack",
        "resolution": "the pillows folded back into adventure books before the lamp could burn the dust",
        "ending": "the adventure shelf stood straight, with one golden speck trapped under the rug",
    },
    {
        "id": "tiny_books",
        "object": "the science books",
        "transformation": "the science books had shrunk to the size of buttons",
        "omen": "a magnifying glass rolled from the locked cabinet before anyone touched it",
        "danger": "the tiny books were slipping through the floor vents into the cellar",
        "clue": "their covers showed damp footprints, although the floor was dry",
        "method": "covered the vents and traced the footprints toward the rain barrel",
        "complication": "a broom swept the little books toward the cellar stairs",
        "turn": "placed a cardboard ramp in the broom's path and caught the books in a basket",
        "resolution": "the science books grew to their proper size beside the warm radiator",
        "ending": "the magnifying glass sat on the science shelf like a watchful eye",
    },
    {
        "id": "talking_maps",
        "object": "the map books",
        "transformation": "the map books had opened their pages and begun arguing aloud",
        "omen": "a compass spun beside the map shelf while the library clock ran backward",
        "danger": "the arguing maps were sending visitors toward the wrong doors",
        "clue": "every false route began with a red dot near the magic atlas",
        "method": "covered the red dots and compared the routes with the real hallway",
        "complication": "the maps shouted louder when the atlas was moved",
        "turn": "asked the librarian to hold the atlas while Luna marked the true door",
        "resolution": "the maps folded shut and pointed quietly toward the reading room",
        "ending": "the compass needle rested on north beneath the library clock",
    },
]


ASP_RULES = r"""
needs_investigation :- library, havoc, transformed_object.
safe_solution :- needs_investigation, clue, careful_method, witness.
valid_story :- safe_solution.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a cautionary detective story about magical library havoc."
    )
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--librarian", choices=LIBRARIAN_NAMES)
    parser.add_argument("--library", choices=LIBRARY_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        hero_name=name,
        librarian_name=args.librarian or rng.choice(LIBRARIAN_NAMES),
        library_name=args.library or rng.choice(LIBRARY_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The detective must be a known young investigator.")
    if params.librarian_name not in LIBRARIAN_NAMES:
        raise StoryError("The witness must be a known librarian.")
    if params.library_name not in LIBRARY_NAMES:
        raise StoryError("The investigation needs a known library.")
    if params.place not in PLACES:
        raise StoryError("The library must stand in a known place.")


def make_world(params: StoryParams) -> LibraryWorld:
    world = LibraryWorld(params.library_name, params.place)
    world.entities["hero"] = Entity("hero", "detective", params.hero_name)
    world.entities["librarian"] = Entity("librarian", "witness", params.librarian_name)
    world.entities["library"] = Entity("library", "place", params.library_name)
    world.facts.update(
        {
            "hero": params.hero_name,
            "librarian": params.librarian_name,
            "library": params.library_name,
            "place": params.place,
            "resolved": False,
        }
    )
    world.meters["disorder"] = 1
    world.meters["danger"] = 1
    world.memes["worry"] = 1
    world.memes["curiosity"] = 1
    return world


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("library"),
            asp.fact("havoc"),
            asp.fact("transformed_object"),
            asp.fact("clue"),
            asp.fact("careful_method"),
            asp.fact("witness"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/0."))
    return bool(asp.atoms(model, "valid_story"))


def choose_scene(world: LibraryWorld, rng: random.Random) -> None:
    scene = rng.choice(SCENES)
    world.facts["scene"] = scene
    world.facts["award"] = rng.choice(AWARDS)
    world.shelves["mystery"] = scene["object"]


def intro(world: LibraryWorld) -> str:
    hero = world.facts["hero"]
    library = world.facts["library"]
    place = world.facts["place"]
    return (
        f"At {place}, {hero} loved solving small mysteries in {library}. "
        f"One afternoon, magical havoc swept through the library, and the shelves began to tremble."
    )


def investigate(world: LibraryWorld) -> str:
    scene = world.facts["scene"]
    world.meters["clues"] += 1
    world.memes["curiosity"] += 1
    return (
        f"The first clue was {scene['omen']}. "
        f"{hero_name(world)} noticed that {scene['clue']}."
    )


def hero_name(world: LibraryWorld) -> str:
    return str(world.facts["hero"])


def dialogue(world: LibraryWorld) -> str:
    scene = world.facts["scene"]
    hero = world.facts["hero"]
    librarian = world.facts["librarian"]
    world.memes["trust"] += 1
    return (
        f'"Do not grab the spell book," said {librarian}. '
        f'"The old label says magic grows wild when people rush." '
        f'"Then we need a careful plan," said {hero}. '
        f'"I will {scene["method"]}."'
    )


def solve(world: LibraryWorld) -> str:
    scene = world.facts["scene"]
    hero = world.facts["hero"]
    librarian = world.facts["librarian"]
    world.meters["disorder"] = 0
    world.meters["danger"] = 0
    world.meters["calm"] = 1
    world.memes["patience"] += 1
    world.memes["relief"] += 1
    world.facts["resolved"] = True
    return (
        f"{hero} began the plan, but {scene['complication']}. "
        f"Instead of using a bigger spell, {hero} {scene['turn']}. "
        f"At last, {scene['resolution']}. "
        f"{scene['ending'].capitalize()}. "
        f'{librarian} handed {hero} {world.facts["award"]}. '
        f'"You solved the mystery because you noticed the warning," said {librarian}.'
    )


def tell_story(params: StoryParams) -> LibraryWorld:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    choose_scene(world, rng)
    scene = world.facts["scene"]
    parts = [
        intro(world),
        f"The transformation was startling: {scene['transformation']}. "
        f"Their strange movement made the havoc worse.",
        investigate(world),
        dialogue(world),
        solve(world),
    ]
    rng.shuffle(parts[1:4])
    world.facts["story"] = "\n\n".join(parts)
    world.facts["scene_id"] = scene["id"]
    return world


def prompts(world: LibraryWorld) -> list[str]:
    scene = world.facts["scene"]
    return [
        'Write a detective story using the words "library" and "havoc".',
        f"Describe how {world.facts['hero']} investigates a magical transformation of {scene['object']}.",
        "Make the story cautionary: careful observation should solve the problem better than a reckless spell.",
    ]


def story_qa(world: LibraryWorld) -> list[QAItem]:
    scene = world.facts["scene"]
    hero = world.facts["hero"]
    librarian = world.facts["librarian"]
    return [
        QAItem(
            question=f"What magical transformation caused havoc in {world.name}?",
            answer=f"The transformation changed {scene['object']} so that {scene['transformation']}.",
        ),
        QAItem(
            question=f"What clue did {hero} notice during the investigation?",
            answer=f"{hero} noticed that {scene['clue']}, after seeing that {scene['omen']}.",
        ),
        QAItem(
            question=f"What did {librarian} warn {hero} about?",
            answer=f"{librarian} warned {hero} not to rush or grab the spell book because the old magic grew wilder when people acted carelessly.",
        ),
        QAItem(
            question=f"How did {hero} stop the magical havoc?",
            answer=f"{hero} {scene['method']}, then {scene['turn']}. This careful choice allowed {scene['resolution']}.",
        ),
        QAItem(
            question=f"What proved that the library was safe again?",
            answer=f"{scene['ending'].capitalize()}. {librarian} also gave {hero} {world.facts['award']} for solving the mystery.",
        ),
    ]


def world_qa(world: LibraryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a library?",
            answer="A library is a place where people can borrow, read, and care for books and other information.",
        ),
        QAItem(
            question="What is havoc?",
            answer="Havoc is wild confusion or damage that makes a place difficult to use safely.",
        ),
        QAItem(
            question="Why can magic require caution?",
            answer="Magic can require caution because a careless action may produce a larger and stranger result than intended.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: LibraryWorld) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"library={world.name}",
            f"place={world.place}",
            f"shelves={world.shelves}",
            f"meters={world.meters}",
            f"memes={world.memes}",
            f"resolved={world.facts.get('resolved')}",
        ]
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    if not asp_valid():
        print("ASP gate rejected the valid library investigation.")
        return 1
    sample = generate(
        StoryParams(
            hero_name="Luna",
            librarian_name="Ms. Bell",
            library_name="Moonbeam Library",
            place="the town square",
            seed=7,
        )
    )
    checks = ["library", "havoc", "magic", "transformation", "careful"]
    if not all(word in sample.story.lower() for word in checks):
        print("Generated story omitted a required world concept.")
        return 1
    if not sample.world or not sample.world.facts.get("resolved"):
        print("Generated story did not resolve its world state.")
        return 1
    print("OK: ASP and Python gates agree; generated story resolves.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/0 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("Luna", "Ms. Bell", "Moonbeam Library", "the town square", base_seed),
            StoryParams("Milo", "Mr. Reed", "The Lantern Library", "Willow Lane", base_seed + 1),
            StoryParams("Nia", "Ada Quill", "Maple Street Library", "the old market", base_seed + 2),
            StoryParams("Theo", "Mara Page", "The Quiet Library", "the hilltop", base_seed + 3),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params_list.append(resolve_params(args, rng))

    samples = [generate(params) for params in params_list]

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
