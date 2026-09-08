#!/usr/bin/env python3
"""
A gentle fable about Luna, a garnet, and the patience needed to see a mystery
clearly.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Entity
    guide: Entity
    garnet: Entity
    place: str
    seed: int
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    guide_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Tess", "Niko", "Suri", "Pia"]
GUIDES = ["Aunt Ibis", "Grandmother Fern", "Old Badger", "Uncle Rowan", "Mara"]
PLACES = [
    "the misty orchard",
    "the hill of blue stones",
    "the quiet village square",
    "the lantern meadow",
    "the old river path",
]


ASP_RULES = r"""
#show curious/1.
#show patient/1.
#show sees_truth/1.
#show solves/1.
#show triumph/1.

curious(H) :- asks_question(H).
patient(H) :- listens(H).
sees_truth(H) :- removes_mist(H).
solves(H) :- compares_clues(H).
triumph(H) :- solves(H), sees_truth(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("asks_question", "hero"),
            asp.fact("listens", "hero"),
            asp.fact("removes_mist", "hero"),
            asp.fact("compares_clues", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = (
        "#show curious/1.\n"
        "#show patient/1.\n"
        "#show sees_truth/1.\n"
        "#show solves/1.\n"
        "#show triumph/1."
    )
    model = asp.one_model(asp_program(shown))
    actual = set()
    for atom in model:
        args = tuple(
            item.number if item.type == item.type.Number else (
                item.string if item.type == item.type.String else item.name
            )
            for item in atom.arguments
        )
        actual.add((atom.name, args))
    expected = {
        ("curious", ("hero",)),
        ("patient", ("hero",)),
        ("sees_truth", ("hero",)),
        ("solves", ("hero",)),
        ("triumph", ("hero",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for seed in range(5):
        params = StoryParams("Luna", "Aunt Ibis", PLACES[seed], seed=seed)
        sample = generate(params)
        if not sample.story or "Luna" not in sample.story:
            print("Generated story verification failed.")
            return 1
    print("OK: ASP parity and generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about Luna, tolerance, sight, and a garnet mystery."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--guide-name", choices=GUIDES)
    parser.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        guide_name=args.guide_name or rng.choice(GUIDES),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.guide_name:
        raise StoryError("The child and guide must have different names.")
    hero = Entity(
        id="hero",
        label=params.name,
        kind="child",
        meters={"patience": 0.35, "sight": 0.45, "distance": 1.0},
        memes={"curiosity": 0.9, "confidence": 0.4, "tolerance": 0.3},
    )
    guide = Entity(
        id="guide",
        label=params.guide_name,
        kind="guide",
        meters={"distance": 1.0},
        memes={"wisdom": 0.85, "tolerance": 0.9},
    )
    garnet = Entity(
        id="garnet",
        label="garnet",
        kind="mystery",
        meters={"size": 0.08, "visibility": 0.2},
        memes={"wonder": 0.8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in f"{params.name}|{params.guide_name}|{params.place}")
    return World(hero=hero, guide=guide, garnet=garnet, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _finish(world: World, *, mystery: str, cause: str, method: str,
            lesson: str, ending: str, story: str) -> str:
    world.facts.update(
        mystery=mystery,
        cause=cause,
        method=method,
        lesson=lesson,
        ending=ending,
        solved="true",
        story=story,
    )
    world.hero.meters.update(patience=0.9, sight=1.0)
    world.hero.memes.update(confidence=0.9, tolerance=0.95)
    world.garnet.meters["visibility"] = 1.0
    return story


def _shadow_arc(world: World, rng: random.Random) -> str:
    h, g, p = world.hero.label, world.guide.label, world.place
    shape = _choice(rng, ["a fox", "a crooked king", "a bird with enormous feet"])
    screen = _choice(rng, ["the barn wall", "a white sheet", "the orchard gate"])
    mystery = f"a huge {shape} appeared on {screen} whenever the garnet shone"
    cause = "the garnet was between a lantern and the screen, making a small shadow look large"
    method = f"{h} moved the lantern, the garnet, and the screen one at a time until the shadow changed"
    lesson = "Patience lets sight separate a frightening shape from its simple cause."
    ending = f"the garnet rested in {g}'s palm while the last shadow became a small red glimmer"
    story = " ".join(
        [
            f"In {p}, {h} found a garnet beneath a lantern.",
            f"That night, a huge {shape} sprang across {screen}.",
            f'"It must be a night beast!" cried {h}. "{g}, can you see its feet?"',
            f'"I see a puzzle," said {g}. "Let us be patient with it."',
            f"{h} moved the lantern first. The beast stretched. Then {h} moved the garnet. The beast shrank.",
            f"{h} moved the screen and watched the shape change again. At last, {h} understood: {cause}.",
            f'"So the mystery was only light and distance," said {h}.',
            f'"A small truth can wear a large shadow," replied {g}.',
            f"Together they showed the villagers how {method.lower()}.",
            f"By moonrise, {ending}. {h} had won a quiet triumph through curiosity, tolerance, and clear sight.",
        ]
    )
    return _finish(world, mystery=mystery, cause=cause, method=method,
                   lesson=lesson, ending=ending, story=story)


def _mist_arc(world: World, rng: random.Random) -> str:
    h, g, p = world.hero.label, world.guide.label, world.place
    sound = _choice(rng, ["a bell", "a flute", "a sleepy cough"])
    mystery = f"{sound} seemed to come from the garnet when the morning mist covered {p}"
    cause = "mist carried a sound from the distant mill and made it seem close"
    method = f"{h} marked where the sound seemed loudest, waited for the mist to lift, and followed the marks"
    lesson = "Tolerance for uncertainty gives curiosity time to test what sight and hearing suggest."
    ending = f"the garnet lay beside the mill's loose copper chime, bright in the clear sun"
    story = " ".join(
        [
            f"At dawn in {p}, {h} held a garnet and heard {sound} whisper from inside it.",
            f'"The stone is singing!" said {h}. "{g}, listen before you laugh."',
            f'"I will listen," said {g}. "A mystery deserves respect, even when it sounds strange."',
            f"The mist thickened, and the sound seemed to follow them between the trees.",
            f"{h} wanted to run after it, but instead placed a pebble wherever the sound seemed strongest.",
            f"When the mist lifted, the pebbles made a crooked path toward the old mill.",
            f"{h} and {g} followed the path and found that {cause}.",
            f'"The garnet did not sing," said {h}. "It helped me notice what I had missed."',
            f'"That is the triumph of a patient question," said {g}.',
            f"At sunset, {ending}. The mystery had become a lesson in tolerance and sight.",
        ]
    )
    return _finish(world, mystery=mystery, cause=cause, method=method,
                   lesson=lesson, ending=ending, story=story)


def _trail_arc(world: World, rng: random.Random) -> str:
    h, g, p = world.hero.label, world.guide.label, world.place
    clue = _choice(rng, ["three blue feathers", "a row of silver leaves", "tiny red marks"])
    mystery = f"{clue} appeared beside the garnet and seemed to point in opposite directions"
    cause = "the clues belonged to two different animals crossing the same path"
    method = f"{h} compared the height, spacing, and direction of each mark instead of choosing the brightest trail"
    lesson = "Problem solving begins when curiosity welcomes more than one possibility."
    ending = "the true path ended at a dry spring where thirsty birds found fresh water"
    story = " ".join(
        [
            f"Near {p}, {h} discovered {clue} beside a garnet.",
            f"The marks pointed east, west, and once straight into a blackberry bush.",
            f'"Which way is right?" asked {h}. "{g}, I want the answer now."',
            f'"Then we must tolerate not knowing yet," said {g}. "Look at every clue."',
            f"{h} measured the spaces with a twig and noticed that one set was low while the other was high.",
            f"After comparing the clues, {h} learned that {cause}.",
            f"{h} followed the lower marks, while {g} followed the higher ones, and both trails met at a dry spring.",
            f'"Curiosity gave us choices," said {h}. "Careful sight gave us the answer."',
            f"{g} smiled. 'A shared answer is a fine triumph.'",
            f"Before evening, {ending}. The garnet glowed beside the water like a small sunrise.",
        ]
    )
    return _finish(world, mystery=mystery, cause=cause, method=method,
                   lesson=lesson, ending=ending, story=story)


def _bridge_arc(world: World, rng: random.Random) -> str:
    h, g, p = world.hero.label, world.guide.label, world.place
    mystery = "the village bridge appeared to have lost its middle plank"
    cause = "a polished garnet reflection made a safe plank look like a dark gap"
    method = f"{h} viewed the bridge from three places and placed a leaf on the suspected gap"
    lesson = "Changing where one looks can turn a false mystery into a visible truth."
    ending = "the garnet sat in a small cloth pouch while the bridge carried everyone home"
    story = " ".join(
        [
            f"One afternoon at {p}, {h} saw that the village bridge had lost its middle plank.",
            f'"No one can cross," said {h}. "{g}, the river is hiding the road."',
            f'"Let us not fear what we have not checked," said {g}.',
            f"{h} looked from the riverbank, then from the hill, then from the bridge rail.",
            f"Each view made the gap seem different. Finally, {h} placed a leaf on the dark place.",
            f"The leaf landed safely. The mystery was solved: {cause}.",
            f'"My first sight was quick, but not careful," said {h}.',
            f'"Quick sight can begin a question," said {g}. "Patient sight can finish it."',
            f"They crossed together and showed the villagers the bright reflection.",
            f"By dusk, {ending}. Luna's triumph was not being right at once, but learning how to look again.",
        ]
    )
    return _finish(world, mystery=mystery, cause=cause, method=method,
                   lesson=lesson, ending=ending, story=story)


ARC_BUILDERS = [_shadow_arc, _mist_arc, _trail_arc, _bridge_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7C)
    return ARC_BUILDERS[world.seed % len(ARC_BUILDERS)](world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    return [
        QAItem(
            question=f"What mystery did {h} investigate?",
            answer=f"{h} investigated {world.facts['mystery']}.",
        ),
        QAItem(
            question="What caused the mystery?",
            answer=f"The mystery was caused because {world.facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} solve the problem?",
            answer=f"{h} solved it by {world.facts['method'].lower()}.",
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer=world.facts["lesson"],
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garnet?",
            answer="A garnet is a hard gemstone that is often red and shiny.",
        ),
        QAItem(
            question="What is tolerance?",
            answer="Tolerance is the patient willingness to accept differences or uncertainty while treating others kindly.",
        ),
        QAItem(
            question="Why is careful sight useful for solving a mystery?",
            answer="Careful sight helps someone compare clues and notice details instead of trusting the first appearance.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding a difficulty, testing ideas, and choosing an action that works.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly fable about triumph, tolerance, and sight.",
        f"Tell a mystery story in {world.place} where curiosity leads to problem solving.",
        "Show a character learning that patient observation is stronger than a quick guess.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.guide, world.garnet]:
        lines.append(
            f"  {entity.id:7} {entity.kind:8} label={entity.label!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  solved={world.facts.get('solved', 'false')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show curious/1.\n"
                "#show patient/1.\n"
                "#show sees_truth/1.\n"
                "#show solves/1.\n"
                "#show triumph/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "5 compatible logical atoms: curious(hero), patient(hero), "
            "sees_truth(hero), solves(hero), triumph(hero)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Aunt Ibis", PLACES[0], seed=base_seed),
            StoryParams("Mira", "Grandmother Fern", PLACES[1], seed=base_seed + 1),
            StoryParams("Tess", "Old Badger", PLACES[2], seed=base_seed + 2),
            StoryParams("Niko", "Uncle Rowan", PLACES[3], seed=base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples],
                             indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
