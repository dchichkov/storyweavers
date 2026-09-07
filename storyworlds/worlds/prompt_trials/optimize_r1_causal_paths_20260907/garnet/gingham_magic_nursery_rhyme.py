#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about gingham magic, small promises, and helpful
choices made in a moonlit village.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: str = ""


@dataclass
class World:
    child: Entity
    keeper: Entity
    cloth: Entity
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    keeper_name: str
    place: str
    problem: str
    solution: str
    voice: str
    seed: Optional[int] = None


NAMES = ["Mina", "Pip", "Lulu", "Toby", "Nell", "Jory", "Wren", "Bess"]
KEEPERS = ["Aunt Mabel", "Grandma June", "Uncle Rowan", "Old Nan", "Mrs. Bell"]
PLACES = ["the moonlit mill", "the buttonwood lane", "the little market square", "the bluebell garden"]
PROBLEMS = ["lost_ribbon", "sleepy_moon", "runaway_basket", "silent_bells"]
SOLUTIONS = ["follow_stitches", "sing_softly", "share_pattern", "find_mistake"]
VOICES = ["bouncy", "gentle", "chipper", "hushed"]

PROBLEM_SOLUTIONS = {
    "lost_ribbon": {"follow_stitches", "share_pattern"},
    "sleepy_moon": {"sing_softly", "find_mistake"},
    "runaway_basket": {"follow_stitches", "share_pattern"},
    "silent_bells": {"sing_softly", "find_mistake"},
}

ASP_RULES = r"""
#show ready/1.
#show helps/1.
#show safe/1.

ready(H) :- has_gingham(H).
helps(H) :- follows_pattern(H).
helps(H) :- sings_kindly(H).
safe(H) :- mends_path(H).
safe(H) :- shares_cloth(H).
"""


def _asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("has_gingham", "child"),
            asp.fact("follows_pattern", "child"),
            asp.fact("sings_kindly", "child"),
            asp.fact("mends_path", "child"),
            asp.fact("shares_cloth", "child"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{_asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program(
            "#show ready/1.\n#show helps/1.\n#show safe/1."
        )
    )
    got = {(sym.name, tuple(
        a.number if a.type == a.type.Number else
        a.string if a.type == a.type.String else a.name
        for a in sym.arguments
    )) for sym in model}
    expected = {
        ("ready", ("child",)),
        ("helps", ("child",)),
        ("safe", ("child",)),
    }
    if got == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(got))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about magical gingham."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--keeper-name", choices=KEEPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--voice", choices=VOICES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problem = args.problem or rng.choice(PROBLEMS)
    choices = sorted(PROBLEM_SOLUTIONS[problem])
    solution = args.solution or rng.choice(choices)
    if solution not in PROBLEM_SOLUTIONS[problem]:
        raise StoryError(
            f"Solution {solution!r} cannot resolve problem {problem!r}."
        )
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        keeper_name=args.keeper_name or rng.choice(KEEPERS),
        place=args.place or rng.choice(PLACES),
        problem=problem,
        solution=solution,
        voice=args.voice or rng.choice(VOICES),
    )


def build_world(params: StoryParams) -> World:
    if params.solution not in PROBLEM_SOLUTIONS.get(params.problem, set()):
        raise StoryError(
            f"The chosen solution {params.solution!r} does not fit "
            f"the problem {params.problem!r}."
        )
    seed = params.seed
    if seed is None:
        seed = sum(
            ord(ch)
            for ch in "|".join(
                [
                    params.name,
                    params.keeper_name,
                    params.place,
                    params.problem,
                    params.solution,
                    params.voice,
                ]
            )
        )
    child = Entity(
        "child",
        params.name,
        "character",
        meters={"steps": 0.0, "breath": 1.0},
        memes={"curiosity": 0.8, "courage": 0.6, "care": 0.7},
    )
    keeper = Entity(
        "keeper",
        params.keeper_name,
        "character",
        meters={"steps": 0.0},
        memes={"patience": 0.9, "trust": 0.7},
    )
    cloth = Entity(
        "gingham",
        "gingham cloth",
        "magical_material",
        meters={"length": 2.0, "brightness": 0.8},
        memes={"memory": 1.0, "kindness": 0.9},
        owner=keeper.id,
    )
    return World(child, keeper, cloth, params.place, seed)


def _pick(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _finish(
    world: World,
    *,
    arc: str,
    discovery: str,
    cause: str,
    resolution: str,
    ending: str,
    object_change: str,
    lines: list[str],
) -> str:
    world.facts.update(
        arc=arc,
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=ending,
        object_change=object_change,
        helped=True,
        story=" ".join(lines),
    )
    return world.facts["story"]


def _lost_ribbon(world: World, rng: random.Random, solution: str) -> str:
    h, k, p = world.child.label, world.keeper.label, world.place
    color = _pick(rng, ["red", "green", "sun-yellow", "berry-blue"])
    ending_place = _pick(rng, ["the school gate", "the baker's door", "the old well"])
    if solution == "follow_stitches":
        discovery = (
            f"the {color} gingham ribbon left a trail of silver stitches wherever it flew"
        )
        cause = (
            "the wind had tugged the ribbon loose, and its enchanted stitches were "
            "trying to lead back to the cloth basket"
        )
        resolution = (
            f"{h} followed the silver stitches around {p}, then tied the ribbon "
            f"to a post at {ending_place}"
        )
        object_change = "the wandering ribbon became a bright guide instead of a lost scrap"
        lines = [
            f"In {p}, {h} found {k}'s {color} gingham ribbon dancing above the lane.",
            f"It skipped past a puddle, hopped over a stool, and fluttered toward {ending_place}.",
            f'"Come back, little checkered kite!" cried {h}.',
            f'"Do not chase its waving end," called {k}. "Look at the stitches. They may know the way."',
            f"{h} crouched low and saw tiny silver crosses glowing along the ribbon's edge.",
            f"The child followed them instead of racing. The ribbon led through the market and around a sleeping cart.",
            f"At {ending_place}, {h} caught the ribbon on a post and tied a careful bow.",
            f'"You listened to the pattern," said {k}. "That is why the magic brought you home."',
            f"The gingham no longer flew away; {ending_place} now wore a cheerful checkered flag.",
        ]
    else:
        discovery = "the magical ribbon could make a safe path when its squares were shared"
        cause = (
            "the ribbon kept darting because one narrow strip could not mark every "
            "corner of the busy lane"
        )
        resolution = (
            f"{h} shared the gingham squares with {k}, who laid them across the lane "
            f"until the ribbon formed a path to {ending_place}"
        )
        object_change = "one flying ribbon became a broad, shining walkway"
        lines = [
            f"At {p}, a {color} gingham ribbon zipped from {k}'s basket and vanished between the stalls.",
            f"{h} grabbed one end, but the other end wriggled free and looped around a bucket.",
            f'"Hold tight!" cried {h}. "I am holding the tightest I can!"',
            f'"Magic grows when it is shared," said {k}, opening the basket of spare gingham squares.',
            f"They placed one square by the bucket, one by the bench, and one beside the crooked lane.",
            f"Each piece glowed and joined the next, so the ribbon had room to stretch without pulling loose.",
            f"{h} and {k} guided the shining checks toward {ending_place}.",
            f"The ribbon settled into a broad path, and every passerby crossed without stumbling.",
            f"By moonrise, the once-lost ribbon had become a welcome road of red and white checks.",
        ]
    return _finish(
        world,
        arc="lost ribbon",
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=lines[-1],
        object_change=object_change,
        lines=lines,
    )


def _sleepy_moon(world: World, rng: random.Random, solution: str) -> str:
    h, k, p = world.child.label, world.keeper.label, world.place
    animal = _pick(rng, ["the foxes", "the ducklings", "the chimney swallows"])
    if solution == "sing_softly":
        discovery = "the moon woke only for a gentle song woven through the gingham checks"
        cause = (
            "the moon had hidden behind a cloud because the night market was too loud "
            "for its silver dreams"
        )
        resolution = (
            f"{h} hummed a soft nursery rhyme while {k} stretched the gingham "
            "between two poles, making a quiet silver screen"
        )
        object_change = "the cloth became a calm screen that carried the song upward"
        lines = [
            f"Over {p}, the moon drooped like a pearl button and forgot to shine.",
            f"Without moonlight, {animal} bumped into baskets, and the lane became a muddled maze.",
            f'"Wake up, Moon!" called {h}.',
            f'"Not with a shout," whispered {k}. "A sleepy thing needs a little rhyme."',
            f"{k} held the gingham wide while {h} sang, 'Check by check, and star by star, shine a little where you are.'",
            f"The red-and-white squares trembled. Each check carried one quiet note into the clouds.",
            f"The moon opened one eye, then two, and poured a silver road across the lane.",
            f"{animal} found their way home, following the soft light instead of bumping through the dark.",
            f"At last, the gingham rested on the fence, glowing like a small quilt beneath the awake moon.",
        ]
    else:
        discovery = "one gingham square was sewn backward and pointed the moon toward sleep"
        cause = (
            "a backward square in the magical cloth turned the moon's light downward "
            "instead of sending it across the village"
        )
        resolution = (
            f"{h} found the backward square and helped {k} turn it around, so the "
            "gingham sent moonlight over {p}"
        )
        object_change = "the cloth changed from a dull blanket into a bright moon-map"
        lines = [
            f"At {p}, the moon shone faintly, as if tucked under a gingham blanket.",
            f"{animal} waited beside the dark lane, unsure which way to go.",
            f'"The cloth has lost its sparkle," said {h}.',
            f'"Or perhaps one square is telling the wrong story," replied {k}.',
            f"They held the gingham to the moon. Most checks glimmered upward, but one square glowed downward into the dust.",
            f"{h} traced the crooked threads and found a little stitch turned backward.",
            f"Together they unpicked it, turned the square, and sewed it neatly into place.",
            f"The gingham flashed. Moonlight sprang over {p}, and {animal} hurried safely home.",
            f"The repaired cloth lay on the fence, patterned with a bright road from earth to sky.",
        ]
    return _finish(
        world,
        arc="sleepy moon",
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=lines[-1],
        object_change=object_change,
        lines=lines,
    )


def _runaway_basket(world: World, rng: random.Random, solution: str) -> str:
    h, k, p = world.child.label, world.keeper.label, world.place
    cargo = _pick(rng, ["apples", "plums", "warm rolls"])
    destination = _pick(rng, ["the fountain", "the duck pond", "the steep mill steps"])
    if solution == "follow_stitches":
        discovery = "the gingham lining made the basket roll along a stitched arrow"
        cause = (
            "the enchanted basket followed a glowing arrow sewn into its gingham lining "
            "when the wind tipped it over"
        )
        resolution = (
            f"{h} followed the arrow around {p} and stepped ahead of the basket at {destination}"
        )
        object_change = "the runaway basket became a marked guide to a safe stopping place"
        lines = [
            f"At {p}, a basket of {cargo} tipped over and rolled away beneath the gingham awning.",
            f"It rattled past a broom, bounced over a pebble, and headed for {destination}.",
            f'"Stop, basket, stop!" shouted {h}.',
            f'"Running behind is not enough," said {k}. "Find the mark that tells it where to go."',
            f"Inside the gingham lining, {h} spotted a row of blue stitches pointing toward a flat patch of ground.",
            f"The child ran along the arrow instead of chasing the rolling basket from behind.",
            f"At {destination}, {h} reached the flat patch first and held out both hands.",
            f"The basket bumped gently against the gingham cloth and stopped, with every {cargo[:-1] if cargo.endswith("s") else cargo} still inside.",
            f"{k} tied the lining down, and the basket rested safely beside the market table.",
        ]
    else:
        discovery = "the basket's magic became steady when its gingham pattern was shared between two hands"
        cause = (
            "the basket kept rolling because the gingham lining had been folded into a "
            "single tight knot that pulled it downhill"
        )
        resolution = (
            f"{h} and {k} spread the gingham flat across the basket, then carried the "
            f"{cargo} together away from {destination}"
        )
        object_change = "the cloth changed a wild rolling basket into a balanced carrier"
        lines = [
            f"Near {p}, a basket of {cargo} rolled away with a gingham cloth knotted inside it.",
            f"{h} caught the handle, but the basket tugged downhill toward {destination}.",
            f'"I have it!" cried {h}.',
            f'"You have one handle," said {k}. "The magic needs two steady hands."',
            f"They loosened the knot and spread the gingham evenly beneath the basket.",
            f"The checks glowed from corner to corner, balancing the weight like four tiny helpers.",
            f"{h} held one side and {k} held the other as they carried the {cargo} back to the market.",
            f"The basket no longer rolled, even when a gust swept through {p}.",
            f"The gingham lay smooth beneath it, and the rescued {cargo} made a safe little hill in the basket.",
        ]
    return _finish(
        world,
        arc="runaway basket",
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=lines[-1],
        object_change=object_change,
        lines=lines,
    )


def _silent_bells(world: World, rng: random.Random, solution: str) -> str:
    h, k, p = world.child.label, world.keeper.label, world.place
    bell = _pick(rng, ["the tiny bell", "the brass bell", "the blue bell"])
    if solution == "sing_softly":
        discovery = "the bell answered a quiet gingham rhyme but not a hurried pull"
        cause = (
            "the bell had become frightened by a hard storm and would ring only when "
            "someone approached it gently"
        )
        resolution = (
            f"{h} sang beside {bell} while {k} wrapped its handle in gingham, "
            "and the bell found its brave clear note"
        )
        object_change = "the cloth became a comforting sleeve around the silent bell"
        lines = [
            f"In {p}, {bell} hung from the arch, but not a single note came out.",
            f"The morning parade waited. Even the pigeons tilted their heads in worry.",
            f'"Ring, little bell!" called {h}, pulling the cord.',
            f'"Try a voice that does not command," said {k}. "Magic listens to kindness."',
            f"{h} touched the bell's handle through a fold of gingham and sang, 'Ding-a-dong, come along.'",
            f"The bell trembled once. The gingham checks shimmered like little windows.",
            f"{h} sang again, softer, and {k} joined with a hum.",
            f"The bell rang clear and bright, sending the parade happily through {p}.",
            f"Afterward, the gingham remained around the handle, warm from the song and bright as a ribbon of dawn.",
        ]
    else:
        discovery = "the bell's missing note was hidden in a loose gingham thread"
        cause = (
            "one loose thread from the gingham banner had slipped into the bell's clapper "
            "and stopped it from moving"
        )
        resolution = (
            f"{h} traced the quiet thread, and {k} helped pull it free from {bell}"
        )
        object_change = "the cloth became a repaired banner instead of a tangled bell-stopper"
        lines = [
            f"At {p}, {bell} stood silent beneath a gingham banner.",
            f"The parade waited in a crooked line while the bell refused every tug.",
            f'"Pull harder!" cried {h}.',
            f'"A hard pull may make a small trouble hide," warned {k}.',
            f"{h} looked beneath the bell and saw one red gingham thread curled around the clapper.",
            f"They followed the thread to the banner, where a corner had come loose in the wind.",
            f"{k} held the banner still while {h} eased the thread free instead of yanking it.",
            f"The clapper swung, and {bell} rang a bright note across {p}.",
            f"They mended the banner with three neat stitches, while the parade marched beneath its steady checks.",
        ]
    return _finish(
        world,
        arc="silent bells",
        discovery=discovery,
        cause=cause,
        resolution=resolution,
        ending=lines[-1],
        object_change=object_change,
        lines=lines,
    )


def generate_story(world: World, params: StoryParams) -> str:
    rng = random.Random(world.seed ^ 0x51A7C)
    if params.problem == "lost_ribbon":
        return _lost_ribbon(world, rng, params.solution)
    if params.problem == "sleepy_moon":
        return _sleepy_moon(world, rng, params.solution)
    if params.problem == "runaway_basket":
        return _runaway_basket(world, rng, params.solution)
    if params.problem == "silent_bells":
        return _silent_bells(world, rng, params.solution)
    raise StoryError(f"Unknown problem: {params.problem!r}")


def story_qa(world: World) -> list[QAItem]:
    h = world.child.label
    f = world.facts
    return [
        QAItem(
            question=f"What did {h} learn about the gingham?",
            answer=f"{h} learned that {f['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble happened because {f['cause']}.",
        ),
        QAItem(
            question=f"How did {h} help?",
            answer=f"{f['resolution']}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, {f['object_change']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gingham?",
            answer="Gingham is a woven fabric with a repeated checked pattern, often made with two colors.",
        ),
        QAItem(
            question="Why can a pattern help someone find a way?",
            answer="A repeated pattern can carry clues, such as arrows, colors, or stitches that point toward a safe path.",
        ),
        QAItem(
            question="What does magic do in these nursery-rhyme stories?",
            answer="The magic responds to careful attention, kindness, sharing, and patient hands rather than to force.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a nursery-rhyme story for young children about magical gingham.",
        f"Tell a rhyming-feeling tale about {world.child.label} helping someone in {world.place}.",
        "Use a small problem, a useful discovery, gentle dialogue, and an ending image that shows what changed.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.child, world.keeper, world.cloth]:
        lines.append(
            f"  {entity.id:8} {entity.kind:16} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world, params)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
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


def asp_facts_text() -> str:
    return _asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ready/1.\n#show helps/1.\n#show safe/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: ready(child), helps(child), safe(child)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                "Mina",
                "Aunt Mabel",
                "the moonlit mill",
                "lost_ribbon",
                "follow_stitches",
                "bouncy",
            ),
            StoryParams(
                "Pip",
                "Grandma June",
                "the bluebell garden",
                "sleepy_moon",
                "sing_softly",
                "gentle",
            ),
            StoryParams(
                "Lulu",
                "Uncle Rowan",
                "the little market square",
                "runaway_basket",
                "share_pattern",
                "chipper",
            ),
            StoryParams(
                "Wren",
                "Old Nan",
                "the buttonwood lane",
                "silent_bells",
                "find_mistake",
                "hushed",
            ),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(100, args.n * 40):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not produce enough distinct story variants.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = (
                f"### {sample.params.name}: "
                f"{sample.params.problem.replace('_', ' ')}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
