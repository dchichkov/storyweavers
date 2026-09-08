#!/usr/bin/env python3
"""
A small stand-alone storyworld about a barracuda, a mistaken belief, and kindness.

Seed premise:
A child visits a bright seaside cove and believes a barracuda is chasing everyone.
A silly misunderstanding, a patient helper, and one kind act reveal that the fish
is only guarding a lost shiny lunch box.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    helper: str
    diver: str
    barracuda: str
    object_name: str
    action: int = 0
    premise: int = 0
    joke: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Luna", "Milo", "Nia", "Toby", "Pia", "Sam", "Ivy", "Noah"]
HELPERS = ["Aunt Bea", "Uncle Jo", "Grandma Kit", "Dad", "Mom", "Coach Ray"]
DIVERS = ["Diver Dot", "Captain Finn", "Mara", "Ollie", "Rin"]
BARRACUDAS = ["Benny", "Blue-Tooth", "Spark", "Captain Chomp", "Bubbles"]
OBJECTS = ["a silver lunch box", "a red beach ball", "a yellow sandal", "a shiny spoon"]

ACTIONS = [
    {
        "cause": "the barracuda circled a silver lunch box near the dock",
        "lead": "Near the dock, a barracuda glided past with a silver lunch box bobbing beside it.",
        "risk": "Luna believed the barracuda was chasing swimmers, so everyone froze like statues with wet elbows.",
        "deed": "Luna held up a bright towel as a calm signal while the helper asked everyone to make room.",
        "result": "the diver guided the lunch box toward shore, and the barracuda swam away without bothering anyone",
    },
    {
        "cause": "the barracuda followed a red beach ball that had drifted from the shore",
        "lead": "A red beach ball rolled into the waves, and a barracuda nudged it along with its nose.",
        "risk": "Luna believed the fish was hunting the ball and shouted so loudly that a crab hid under a flip-flop.",
        "deed": "Luna gently asked everyone to step back while the helper used a long beach rake to pull the ball in.",
        "result": "the ball returned to its owner, and the barracuda lost interest and slipped into deeper water",
    },
    {
        "cause": "the barracuda hovered beside a yellow sandal caught in seaweed",
        "lead": "A yellow sandal dangled in the seaweed, and a barracuda kept circling it.",
        "risk": "Luna believed the barracuda wanted a snack, even though the sandal looked much too chewy for anybody.",
        "deed": "Luna told the helper about the seaweed while the diver approached slowly and freed the sandal.",
        "result": "the sandal came loose, and the barracuda swam off as if it had never wanted footwear for lunch",
    },
    {
        "cause": "the barracuda guarded a shiny spoon resting on the sandy bottom",
        "lead": "Under the clear water, a shiny spoon flashed like a tiny moon beside a barracuda.",
        "risk": "Luna believed the flash was a dangerous tooth and hid behind a bucket that was far too small.",
        "deed": "Luna listened when the helper explained the difference between a tooth and a spoon, then helped mark the safe spot.",
        "result": "the diver picked up the spoon, and the barracuda calmly returned to the open sea",
    },
]

PREMISES = [
    "{name} arrived at the sunny cove with {helper} and expected only shells, snacks, and a very serious sand castle.",
    "The tide was low when {name} and {helper} visited the cove. Even the puddles seemed to be wearing little mirrors.",
    "{name} had promised to be brave at the beach, but the promise became wobbly when a dark fin appeared near the dock.",
    "At the cove, {name} met {diver}, who was checking the water and telling jokes to a pelican that did not laugh.",
    "{name} and {helper} came to look for tiny fish. Instead, they found a mystery with fins, bubbles, and one extremely suspicious object.",
]

JOKES = [
    "{helper} whispered, 'Remember, kindness is faster than panic.' {name} nodded, although the nod accidentally bounced a shell off {name}'s knee.",
    "{diver} said, 'A barracuda has teeth, but it does not have a map of your lunch.' {name} replied, 'Good, because my lunch gets lost in my backpack.'",
    "{name} asked, 'Can fish understand kindness?' {diver} answered, 'They understand when we give them space.' The pelican understood none of it and stole a cracker.",
    "{helper} called, 'Slow steps!' {name} took one careful step, then another, and finally one extremely unnecessary tiny penguin step.",
    "'What should we do?' asked {name}. 'Look closely and help gently,' said {helper}. 'And avoid yelling at fish,' added {diver}.",
]

ENDINGS = [
    "By sunset, {name} had learned that a frightening fin can hide a harmless reason. The cove glowed gold, and even the barracuda looked peaceful.",
    "{name} drew a picture of the barracuda beside the rescued object. Under it, {name} wrote, 'Ask kindly before you believe a scary story.'",
    "The beach owner thanked {name} for helping instead of shouting. The barracuda made one last splash, which looked almost like a bow.",
    "On the walk home, {name} practiced saying, 'I can check before I guess.' The sentence sounded wise until a pigeon stole a crumb.",
    "The next morning, the cove was quiet. A silver flash far offshore reminded {name} that kindness had solved more than fear could.",
]

ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

name(N) :- name_value(N).
helper(H) :- helper_value(H).
object(O) :- object_value(O).
barracuda(B) :- barracuda_value(B).

kind_action(A) :- kindness_action(A).
valid(N,O) :- name_value(N), object_value(O), kindness_action(_).
valid_story(N,O,A) :- valid(N,O), kindness_action(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in NAMES:
        lines.append(asp.fact("name_value", value))
    for value in HELPERS:
        lines.append(asp.fact("helper_value", value))
    for value in OBJECTS:
        lines.append(asp.fact("object_value", value))
    for value in BARRACUDAS:
        lines.append(asp.fact("barracuda_value", value))
    for index in range(len(ACTIONS)):
        lines.append(asp.fact("kindness_action", index))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(name, obj) for name in NAMES for obj in OBJECTS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly comedy storyworld about a barracuda and kindness."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--diver", choices=DIVERS)
    parser.add_argument("--barracuda", choices=BARRACUDAS)
    parser.add_argument("--object-name", choices=OBJECTS)
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
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        diver=args.diver or rng.choice(DIVERS),
        barracuda=args.barracuda or rng.choice(BARRACUDAS),
        object_name=args.object_name or rng.choice(OBJECTS),
        action=rng.randrange(len(ACTIONS)),
        premise=rng.randrange(len(PREMISES)),
        joke=rng.randrange(len(JOKES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.action = seed % len(ACTIONS)
    params.premise = (seed // len(ACTIONS)) % len(PREMISES)
    params.joke = (seed // 3) % len(JOKES)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    action = ACTIONS[params.action % len(ACTIONS)]
    values = {
        "name": params.name,
        "helper": params.helper,
        "diver": params.diver,
        "barracuda": params.barracuda,
        "object": params.object_name,
    }

    world = World()
    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            label=params.name,
            memes={"belief": 0.0, "kindness": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(Entity(id="helper", kind="character", label=params.helper))
    diver = world.add(Entity(id="diver", kind="character", label=params.diver))
    fish = world.add(
        Entity(
            id="barracuda",
            kind="animal",
            label=params.barracuda,
            meters={"distance_from_shore": 0.7},
            memes={"calm": 0.8, "mystery": 1.0},
        )
    )
    object_entity = world.add(
        Entity(
            id="lost_object",
            kind="thing",
            label=params.object_name,
            meters={"floating": 0.5},
            memes={"importance": 0.7},
        )
    )

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(
        f"{params.diver} pointed toward the water, where {params.barracuda} moved near {params.object_name}."
    )
    world.say(action["lead"].replace("a silver lunch box", params.object_name)
              .replace("a red beach ball", params.object_name)
              .replace("a yellow sandal", params.object_name)
              .replace("a shiny spoon", params.object_name))

    world.para()
    child.memes["belief"] = 1.0
    fish.memes["mystery"] = 1.0
    object_entity.meters["floating"] = 1.0
    world.say(action["risk"])
    world.say(f'"Is the barracuda coming after us?" asked {params.name}.')
    world.say(f'"No," said {params.helper}. "Let us watch before we decide what it means."')
    world.say(f'"I can help from a safe distance," said {params.diver}.')

    world.para()
    child.memes["kindness"] = 1.0
    child.memes["belief"] = 0.0
    child.memes["relief"] = 1.0
    fish.memes["mystery"] = 0.0
    object_entity.meters["floating"] = 0.0
    world.say(action["deed"])
    world.say(action["result"])
    world.say(JOKES[params.joke % len(JOKES)].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.name,
        helper=params.helper,
        diver=params.diver,
        barracuda=params.barracuda,
        object_name=params.object_name,
        misunderstanding=action["cause"],
        helpful_action=action["deed"],
        resolution=action["result"],
        kindness=True,
        belief_corrected=True,
        resolved=True,
    )

    prompts = [
        "Write a funny child-friendly story about a child who misunderstands a barracuda and learns kindness.",
        f"Tell a comedy story in which {params.name} believes a barracuda is dangerous, then helps solve a seaside mystery.",
        f"Write a story about {params.name}, {params.helper}, and {params.barracuda} that includes a mistaken belief, dialogue, and a kind solution.",
    ]

    story_qa = [
        QAItem(
            question="Why did the moment seem frightening at first?",
            answer=f"It seemed frightening because {action['cause']}. {params.name} believed the barracuda was chasing people.",
        ),
        QAItem(
            question=f"What did {params.name} do to help?",
            answer=f"{params.name} acted kindly by {action['deed'].lower().rstrip('.')}.",
        ),
        QAItem(
            question="What did the characters learn about the barracuda?",
            answer=f"They learned that the barracuda was not attacking anyone; {action['result']}.",
        ),
        QAItem(
            question="How did the conversation change the story?",
            answer=f"{params.helper} encouraged everyone to watch calmly before guessing, so {params.name} changed from fear to careful kindness.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a barracuda?",
            answer="A barracuda is a long, fast sea fish with sharp teeth that lives in warm ocean waters.",
        ),
        QAItem(
            question="Why is it wise to watch before making a guess?",
            answer="Watching carefully can reveal what is really happening and prevent a frightening mistake.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating people, animals, and the world with care and helping when it is safe to do so.",
        ),
        QAItem(
            question="What is comedy?",
            answer="Comedy is a kind of story or performance that uses funny situations, words, or surprises to make people laugh.",
        ),
        QAItem(
            question="How can dialogue help a story?",
            answer="Dialogue lets characters share information and make choices that change what happens next.",
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:14} ({entity.kind:9}) {' '.join(details)}")
    if world.facts:
        lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Aunt Bea", "Diver Dot", "Benny", "a silver lunch box", 0, 0, 0, 0),
        StoryParams("Milo", "Uncle Jo", "Captain Finn", "Blue-Tooth", "a red beach ball", 1, 1, 1, 1),
        StoryParams("Nia", "Grandma Kit", "Mara", "Spark", "a yellow sandal", 2, 2, 2, 2),
        StoryParams("Toby", "Mom", "Ollie", "Captain Chomp", "a shiny spoon", 3, 3, 3, 3),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} valid child-and-object combinations:\n")
        for name, object_name in combinations:
            print(f"  {name:8} -> {object_name}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: the barracuda misunderstanding"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
