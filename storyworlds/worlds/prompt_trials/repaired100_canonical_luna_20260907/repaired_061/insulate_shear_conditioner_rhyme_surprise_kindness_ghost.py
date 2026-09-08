#!/usr/bin/env python3
"""
A gentle ghost storyworld about insulating a chilly attic, shearing a woolly
friend, and discovering that kindness can warm even a wandering rhyme.
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

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    house: str = "Moonbeam House"
    child: str = "Luna"
    helper: str = "Moss"
    ghost: str = "Pale Pip"
    material: str = "wool"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def cap(self) -> str:
        return self.label


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HOUSES = ["Moonbeam House", "Willow Cottage", "Starbell Manor", "Clover Hall"]
CHILDREN = ["Luna", "Mira", "Theo", "Nell"]
HELPERS = ["Moss", "Pip", "Juniper", "Bramble"]
GHOSTS = ["Pale Pip", "Little Echo", "Whisper Belle", "Silver Sam"]
MATERIALS = ["wool", "cotton", "felt", "straw"]

SCENES = [
    {
        "opening": "Every midnight, a cold little breeze sighed down from the attic.",
        "clue": "a silver footprint beside the old quilt",
        "ghost_line": "I rhyme, I roam, I miss my home",
        "mistake": "Luna thought the ghost wanted to frighten everyone away.",
        "reveal": "the ghost was shivering because the attic roof had lost its warm lining",
        "ending": "By morning, the attic held a soft nest of wool and a bright square of sunlight.",
    },
    {
        "opening": "Three pale knocks sounded above the kitchen whenever the moon rose.",
        "clue": "a button shaped like a tiny moon",
        "ghost_line": "Cold in the hall, no warmth at all",
        "mistake": "The family guessed that the ghost was angry with the house.",
        "reveal": "the ghost was searching for a warm place to keep an old sheep bell",
        "ending": "The bell rested in a snug wool pocket, and the midnight knocks became gentle taps.",
    },
    {
        "opening": "A white scarf floated through the hallway without any hands inside it.",
        "clue": "a trail of blue lint leading toward the attic stairs",
        "ghost_line": "Trim the fleece, please, if you please",
        "mistake": "The scarf made everyone wonder whether a storm had entered the house.",
        "reveal": "the ghost needed warm fibers for a blanket that had become thin and torn",
        "ending": "The repaired blanket glimmered on the attic chair like a small friendly cloud.",
    },
    {
        "opening": "The chimney hummed a strange tune after supper.",
        "clue": "a loose thread caught on the chimney latch",
        "ghost_line": "Warm the stone, mend what is gone",
        "mistake": "Luna feared the humming meant the chimney was about to wake up.",
        "reveal": "the ghost had been singing for help because winter air slipped through the attic boards",
        "ending": "The humming changed into a soft lullaby beneath the newly covered roof.",
    },
]


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity("child", "character", "child", params.child, ["curious"]))
    helper = world.add(Entity("helper", "character", "animal", params.helper, ["gentle"]))
    ghost = world.add(Entity("ghost", "character", "ghost", params.ghost, ["lonely"]))
    fleece = world.add(Entity("fleece", "thing", params.material, f"a bundle of {params.material}"))
    world.facts.update(
        child=child,
        helper=helper,
        ghost=ghost,
        fleece=fleece,
        scene=SCENES[(params.seed or 0) % len(SCENES)],
        scene_index=(params.seed or 0) % len(SCENES),
    )
    return world


def narrate(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    fleece: Entity = world.facts["fleece"]  # type: ignore[assignment]
    scene: dict[str, str] = world.facts["scene"]  # type: ignore[assignment]

    child.memes["curiosity"] = 1.0
    helper.memes["kindness"] = 1.0
    ghost.memes["loneliness"] = 1.0
    world.events.append("cold attic discovered")

    world.say(f"At {p.house}, {scene['opening']} {child.cap()} heard it while carrying a candle upstairs.")
    world.say(f"Near the attic door, {child.cap()} found {scene['clue']}. {helper.cap()} padded after her, carrying a basket.")
    world.say(f'"Did you hear that rhyme?" asked {child.cap()}. "{scene["ghost_line"]}," whispered {ghost.cap()} from behind the rafters.')
    world.para()

    world.say(scene["mistake"])
    world.say(f'"Please do not hide," called {child.cap()}. "{scene["ghost_line"]}," answered {ghost.cap()}.')
    world.say(f"The voice was thin, and {child.cap()} noticed {ghost.cap()} was trembling. {scene['reveal']}.")
    world.events.append("kindness chosen")

    world.para()
    world.say(f'"We can help," said {child.cap()}. "{helper.cap()}, bring the {fleece.label}; I will see where the boards let the cold in."')
    world.say(f"{helper.cap()} helped {child.cap()} insulate the drafty attic with the {p.material}. Then they carefully shear a little clean fleece from a friendly sheep outside and washed it with a mild conditioner.")
    world.events.extend(["attic insulated", "wool sheared", "fleece conditioned"])
    child.meters["warmth"] = 1.0
    ghost.memes["trust"] = 1.0
    world.say(f"The conditioner made the fleece soft and fresh, so they wrapped {ghost.cap()} in it without a single scratch.")
    world.say(f'"Your rhyme led us here," said {child.cap()}. "{ghost.cap()}, you are welcome to stay warm."')
    world.para()

    world.events.append("surprise revealed")
    ghost.meters["warmth"] = 1.0
    ghost.memes["joy"] = 1.0
    world.say(f"Then came the surprise: {ghost.cap()} smiled, and the old attic stars began to glow. Each star sang a tiny rhyme: \"Kind hearts share, warm hearts care!\"")
    world.say(f"{ghost.cap()} explained that kindness had been the missing spell. {child.cap()} and {helper.cap()} had not chased the ghost away; they had listened, worked, and made a home feel safe.")
    world.say(scene["ending"])


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle ghost story about {p.child} using kindness, rhyme, and surprise.",
        f"Tell how friends insulate an attic, shear wool, and use conditioner to help a ghost.",
        "Create a child-facing ghost story where listening turns a frightening mystery into friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    fleece: Entity = world.facts["fleece"]  # type: ignore[assignment]
    scene: dict[str, str] = world.facts["scene"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who heard the mystery at {p.house}?",
            answer=f"{child.cap()} heard the strange attic sounds and investigated with {helper.cap()}.",
        ),
        QAItem(
            question=f"What rhyme did {ghost.cap()} repeat?",
            answer=f'{ghost.cap()} repeated, "{scene["ghost_line"]}" to show that the ghost was calling for help.',
        ),
        QAItem(
            question=f"Why did the friends help {ghost.cap()}?",
            answer=f"They noticed that {scene["reveal"]}, so kindness made them choose to help instead of being afraid.",
        ),
        QAItem(
            question="How did the friends make the fleece ready?",
            answer=f"They insulated the attic, carefully sheared clean {p.material}, and washed it with conditioner so it would feel soft.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was that {ghost.cap()} smiled and the attic stars glowed while singing a rhyme about caring.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does insulate mean?",
            answer="To insulate means to add material that helps keep heat in or cold out.",
        ),
        QAItem(
            question="What does shear mean?",
            answer="To shear means to carefully cut wool or hair from an animal.",
        ),
        QAItem(
            question="What is conditioner used for?",
            answer="Conditioner can make cleaned fibers or hair softer and easier to handle.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing that someone needs help and choosing to treat them with care.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line or group of words that has matching or similar ending sounds.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"scene={world.facts['scene_index']}")
    lines.append(f"events={world.events}")
    return "\n".join(lines)


ASP_RULES = r"""
character(child).
character(helper).
character(ghost).
action(insulate).
action(shear).
action(conditioner).
feature(rhyme).
feature(surprise).
feature(kindness).
done(insulate) :- action(insulate).
done(shear) :- action(shear).
done(conditioner) :- action(conditioner).
good_story :- done(insulate), done(shear), done(conditioner),
              feature(rhyme), feature(surprise), feature(kindness).
#show good_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    facts = []
    for value in ["child", "helper", "ghost"]:
        facts.append(asp.fact("character", value))
    for value in ["insulate", "shear", "conditioner"]:
        facts.append(asp.fact("action", value))
    for value in ["rhyme", "surprise", "kindness"]:
        facts.append(asp.fact("feature", value))
    return "\n".join(facts)


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    asp_ok = any(sym.name == "good_story" for sym in model)
    sample = generate(StoryParams(seed=17))
    py_ok = all(
        word in sample.story.lower()
        for word in ["insulate", "shear", "conditioner", "rhyme", "surprise", "kindness"]
    )
    if asp_ok and py_ok:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gentle ghost storyworld about warmth, rhyme, surprise, and kindness."
    )
    parser.add_argument("--house", choices=HOUSES)
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--ghost", choices=GHOSTS)
    parser.add_argument("--material", choices=MATERIALS)
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


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice([item for item in HELPERS if item != child])
    return StoryParams(
        house=args.house or rng.choice(HOUSES),
        child=child,
        helper=helper,
        ghost=args.ghost or rng.choice(GHOSTS),
        material=args.material or rng.choice(MATERIALS),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.child == params.helper:
        raise StoryError("the child and helper must be different characters")
    world = build_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            ("Moonbeam House", "Luna", "Moss", "Pale Pip", "wool"),
            ("Willow Cottage", "Mira", "Pip", "Little Echo", "cotton"),
            ("Starbell Manor", "Theo", "Juniper", "Whisper Belle", "felt"),
            ("Clover Hall", "Nell", "Bramble", "Silver Sam", "straw"),
        ]
        samples = [
            generate(
                StoryParams(
                    house=house,
                    child=child,
                    helper=helper,
                    ghost=ghost,
                    material=material,
                    seed=base_seed + i,
                )
            )
            for i, (house, child, helper, ghost, material) in enumerate(presets)
        ]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 10):
            attempts += 1
            sample_seed = base_seed + attempts
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if not samples:
        raise StoryError("no story samples could be generated")

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
