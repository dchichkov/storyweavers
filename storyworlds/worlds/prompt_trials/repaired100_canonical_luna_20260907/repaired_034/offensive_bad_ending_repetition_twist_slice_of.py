#!/usr/bin/env python3
"""
A small slice-of-life storyworld about an offensive mistake, repeated attempts,
a twist, and a repaired ending.
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    neighbor: str = "Mara"
    place: str = "the apartment courtyard"
    object_name: str = "a chalk sign"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    neighbor: Entity
    object_entity: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Luna", "Ivo", "Nell", "Owen", "Priya", "Sam"]
NEIGHBOR_NAMES = ["Mara", "Theo", "June", "Ben", "Asha", "Kit"]
PLACES = [
    "the apartment courtyard",
    "the shared hallway",
    "the corner laundry room",
    "the little community garden",
]
OBJECTS = ["a chalk sign", "a paper notice", "a painted flowerpot", "a cardboard arrow"]

ARCS = [
    {
        "premise": "Luna was getting ready for the courtyard's small evening potluck",
        "problem": "she wrote a sharp sign telling people not to touch the table",
        "offense": "Mara felt accused when she read the words",
        "repetition": "Luna erased the sign and wrote another version, but it still sounded bossy",
        "clue": "Mara quietly pointed out that the table belonged to everyone",
        "action": "Luna asked Mara what would make the table feel welcoming",
        "twist": "Mara had not been reaching for the food at all; she had been trying to save a bowl from tipping",
        "bad_ending": "The two friends nearly carried their hurt inside and left the table empty",
        "repair": "Luna changed the sign to 'Please help us keep this table steady,' and Mara added a bright drawing of two hands",
        "ending": "By sunset, neighbors placed dishes beneath the friendly sign and thanked one another for making room",
        "question": "Why did Mara touch the table?",
        "answer": "Mara touched the table because she was trying to stop a bowl from tipping, not take anyone's food.",
    },
    {
        "premise": "Luna was sorting clean towels in the shared hallway",
        "problem": "she hung an offensive note saying that careless people should stop leaving baskets around",
        "offense": "Theo recognized his basket and felt embarrassed",
        "repetition": "Luna tried two shorter notes, but each one still blamed someone",
        "clue": "Theo explained that the baskets blocked the door only when the elevator stopped",
        "action": "Luna and Theo measured a safe spot beside the laundry shelf",
        "twist": "Theo had been moving the baskets away from a dripping ceiling pipe",
        "bad_ending": "Without asking, Luna might have thrown away the very baskets protecting the clean towels",
        "repair": "They marked the safe spot and wrote, 'Please park baskets here while the pipe is fixed'",
        "ending": "The hallway stayed clear, and the baskets waited neatly under the new note",
        "question": "Why had Theo moved the baskets?",
        "answer": "Theo moved the baskets to protect the clean towels from a dripping ceiling pipe.",
    },
    {
        "premise": "Luna was painting flowerpots for the community garden",
        "problem": "she told Mara that Mara's crooked pots were ruining the garden",
        "offense": "Mara stopped painting and held her brush very still",
        "repetition": "Luna repeated the criticism in three different ways, hoping one would sound helpful",
        "clue": "Mara showed that every crooked pot had been shaped by a child",
        "action": "Luna asked before offering a suggestion and listened to the children's ideas",
        "twist": "The uneven pots were meant to become a path of friendly faces",
        "bad_ending": "The garden would have lost its happiest row if Luna had painted over them",
        "repair": "Luna added eyes and smiles instead of covering the crooked edges",
        "ending": "The garden path waved with painted faces whenever the afternoon breeze moved the leaves",
        "question": "What was special about the crooked pots?",
        "answer": "The crooked pots had been shaped by children and were meant to form a path of friendly faces.",
    },
    {
        "premise": "Luna was labeling boxes for a building book swap",
        "problem": "she wrote that nobody should bring boring books",
        "offense": "Asha looked down because she had brought a quiet book about clouds",
        "repetition": "Luna replaced the word boring with dull and then sleepy, but the message still hurt",
        "clue": "Asha explained that the cloud book helped her grandmother rest",
        "action": "Luna asked what kinds of books made different readers feel welcome",
        "twist": "The quiet cloud book was the one several neighbors had been hoping to find",
        "bad_ending": "The swap might have sent away a book that many people needed",
        "repair": "Luna changed the label to 'Books for every kind of day'",
        "ending": "The cloud book passed from hand to hand while the box filled with many kinds of stories",
        "question": "Why did Asha value the cloud book?",
        "answer": "Asha valued the cloud book because it helped her grandmother rest.",
    },
]

OPENINGS = [
    "The kettle clicked off just as afternoon light reached the windows",
    "A quiet breeze carried soap and warm bread through the building",
    "The day had no grand adventure planned, only chores and familiar footsteps",
    "Sunlight made a pale square on the floor near the open door",
]

DIALOGUE = [
    (
        "Mara asked, \"Did you mean that sign for me?\"",
        "Luna answered, \"I meant to protect the table, but I can hear how it sounded.\"",
    ),
    (
        "The neighbor said, \"Could we look at the problem together?\"",
        "Luna replied, \"Yes. I made a guess before I asked you.\"",
    ),
    (
        "Mara said, \"That word makes me want to leave.\"",
        "Luna said, \"Then I need to choose words that invite help instead.\"",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about repairing an offensive mistake.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--neighbor", choices=NEIGHBOR_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object-name", choices=OBJECTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    choices = [name for name in NEIGHBOR_NAMES if name != hero]
    neighbor = args.neighbor or rng.choice(choices)
    if hero == neighbor:
        raise StoryError("The hero and neighbor must be different people.")
    return StoryParams(
        hero=hero,
        neighbor=neighbor,
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "person"),
        neighbor=Entity(params.neighbor, "neighbor"),
        object_entity=Entity(params.object_name, "object"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)

    world.hero.memes.update({"hurry": 1.0, "defensiveness": 0.0, "care": 0.0})
    world.neighbor.memes.update({"hurt": 0.0, "trust": 0.0})
    world.object_entity.meters["present"] = 1.0
    world.facts.update({
        "place": p.place,
        "object": p.object_name,
        "problem": arc["problem"],
        "offense": arc["offense"],
        "twist": arc["twist"],
        "resolved": False,
    })

    world.say(f"{rng.choice(OPENINGS)}. In {p.place}, {p.hero} was preparing for an ordinary shared task.")
    world.say(f"{arc['premise']}. The useful thing nearby was {p.object_name}.")
    world.para()

    world.say(f"Then {arc['problem']}. The words were offensive even though {p.hero} wanted to be helpful.")
    world.say(f"{arc['offense']}.")
    world.hero.memes["defensiveness"] = 1.0
    world.neighbor.memes["hurt"] = 1.0
    first, second = rng.choice(DIALOGUE)
    world.say(f"{first} {second}")
    world.say(f"{arc['repetition']}. Repetition did not make the message kinder; it only made the hurt easier to notice.")
    world.para()

    world.say(f"{arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.hero.memes["hurry"] = 0.0
    world.hero.memes["care"] = 1.0
    world.say(f"Here was the twist: {arc['twist']}.")
    world.facts["twist_reveal"] = arc["twist"]
    world.say(f"For a moment, a bad ending seemed close: {arc['bad_ending']}.")
    world.para()

    world.say(f"Instead, {arc['repair']}.")
    world.neighbor.memes["hurt"] = 0.0
    world.neighbor.memes["trust"] = 1.0
    world.facts["repair"] = arc["repair"]
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]
    world.say(f"{arc['ending']}.")
    world.say(f"{p.hero} learned that a careful question can repair what an offensive guess begins.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a gentle slice-of-life story about {params.hero} repairing an offensive mistake with {params.neighbor}.",
        f"Include repetition, a twist, and a possible bad ending before the characters choose a kinder action.",
        f"Set the story in {params.place} and make the ending prove that listening changed the day.",
    ]
    story_qa = [
        QAItem(
            question=f"What offensive thing did {params.hero} do?",
            answer=f"{params.hero} made an offensive choice by saying or writing that {arc['problem'].replace('she ', '')}.",
        ),
        QAItem(
            question=f"Why did the repeated attempts fail?",
            answer=f"The repeated attempts failed because changing a few words did not remove the blame or give {params.neighbor} a chance to explain.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question="What bad ending did the characters avoid?",
            answer=f"They avoided this bad ending: {arc['bad_ending']}.",
        ),
        QAItem(
            question=f"How did {params.hero} repair the mistake?",
            answer=f"{params.hero} repaired it by {arc['repair'].lower()}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does offensive mean in this story?",
            answer="Offensive means hurtful or disrespectful in a way that can make another person feel unwelcome.",
        ),
        QAItem(
            question="Why can repetition be a problem?",
            answer="Repetition can be a problem when repeating the same blaming idea makes hurt stronger instead of solving the cause.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising fact that changes what the characters and reader understand about the problem.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.neighbor, world.object_entity):
        lines.append(
            f"  {entity.name:18} ({entity.kind:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
required(offensive).
required(bad_ending).
required(repetition).
required(twist).
valid(story) :- required(offensive), required(bad_ending),
                 required(repetition), required(twist).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("domain", "slice_of_life"),
            asp.fact("feature", "offensive"),
            asp.fact("feature", "bad_ending"),
            asp.fact("feature", "repetition"),
            asp.fact("feature", "twist"),
        ]
    )


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1
    for params in curated_params():
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1
    print("OK: ASP twin and generated stories are consistent.")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(hero="Luna", neighbor="Mara", place=PLACES[0], object_name=OBJECTS[0], arc=0, seed=101),
        StoryParams(hero="Ivo", neighbor="Theo", place=PLACES[1], object_name=OBJECTS[1], arc=1, seed=202),
        StoryParams(hero="Nell", neighbor="Asha", place=PLACES[3], object_name=OBJECTS[2], arc=3, seed=303),
    ]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print(asp.atoms(asp.one_model(asp_program()), "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        samples = []
        for index in range(max(1, args.n)):
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
