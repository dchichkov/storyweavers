#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a tribe and a gentle transformation.
The tribe learns that a useful change begins with listening, trying, and sharing.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    object_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Luna", "Mara", "Tavi", "Niko", "Sela", "Omi"]
FRIENDS = ["Ari", "Beko", "Cora", "Danu", "Ema", "Faro"]
OBJECTS = ["basket", "drum", "blanket", "clay cup", "garden gate"]

SCENARIOS = [
    {
        "key": "woven_basket",
        "premise": "the tribe had gathered to repair a wide carrying basket before the afternoon berry walk",
        "problem": "the basket kept changing shape whenever someone pulled a reed too tightly",
        "clue": "a loose reed was bending around a smooth stone hidden in the weave",
        "dialogue": "'It is not stubborn,' {name} said. 'It is carrying a secret stone.' '{name},' said {friend}, 'then let us ask the basket what it needs.'",
        "action": "They loosened the tight reeds, removed the stone, and gave each person one small section to weave",
        "result": "the basket became round and strong enough for the berries",
        "ending": "By sunset, the basket rested beside the cooking fire, round as a moon and full of purple berries",
        "lesson": "a change can become easier when a group notices the small thing causing the trouble",
    },
    {
        "key": "drum_skin",
        "premise": "the tribe was preparing a quiet morning song with an old hand drum",
        "problem": "the drum's deep voice had turned into a thin squeak",
        "clue": "the skin was loose on one side after a night of cool air",
        "dialogue": "'The drum has not forgotten its song,' said {friend}. '{name},' answered, 'perhaps it needs a little warmth before it speaks.'",
        "action": "They warmed the drum near the sunny wall, tightened the pegs evenly, and tested one gentle beat at a time",
        "result": "the squeak changed into a soft, steady thump that everyone could follow",
        "ending": "At breakfast, spoons tapped the same gentle rhythm while the drum waited proudly by the doorway",
        "lesson": "patient care can transform a frustrating sound into a shared rhythm",
    },
    {
        "key": "blue_clay",
        "premise": "the tribe was shaping cups from blue clay beside the village path",
        "problem": "the clay cup {object_name} made kept leaning like it wanted to nap",
        "clue": "one side was thicker because a small thumbprint had pushed extra clay there",
        "dialogue": "'It is trying to lie down,' {friend} joked. '{name} replied, 'Then we will help it stand without scolding it.'",
        "action": "They pressed the thick side gently, turned the cup as they worked, and made a broad foot for its base",
        "result": "the leaning cup became a sturdy little cup with a useful rounded foot",
        "ending": "That evening, {object_name} held warm berry tea while its round foot kept it steady on the table",
        "lesson": "a flaw can sometimes become a strength when people reshape it with care",
    },
    {
        "key": "garden_gate",
        "premise": "the tribe was opening the garden for the first watering of the season",
        "problem": "the wooden gate scraped the ground and would not swing wide enough for the water jars",
        "clue": "a twig had grown through the lower hinge during the rainy weeks",
        "dialogue": "'The gate is growing a tail,' said {friend}. '{name} laughed, 'A tail that needs trimming before the jars arrive.'",
        "action": "They cleared the twig, lifted the gate together, and placed a flat stone under the hinge",
        "result": "the gate swung smoothly and let the water jars pass without bumping",
        "ending": "Small wet footprints crossed the garden path as the transformed gate opened and closed with a soft wooden sigh",
        "lesson": "ordinary work can feel new when neighbors solve it together",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), tribe(P), transformation(P), slice_of_life(P), resolved(P).
story_ok(P) :- valid(P), dialogue(P), safe(P), changed(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A tribe transformation slice-of-life storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--object-name", dest="object_name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([x for x in FRIENDS if x != name])
    object_name = args.object_name or rng.choice(OBJECTS)
    if not name.strip():
        raise StoryError("The main character's name cannot be empty.")
    if not friend.strip():
        raise StoryError("The friend's name cannot be empty.")
    return StoryParams(name=name, friend=friend, object_name=object_name)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("params", "p1"),
            asp.fact("tribe", "p1"),
            asp.fact("transformation", "p1"),
            asp.fact("slice_of_life", "p1"),
            asp.fact("dialogue", "p1"),
            asp.fact("safe", "p1"),
            asp.fact("changed", "p1"),
            asp.fact("resolved", "p1"),
        ]
    )


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    valid = set(asp.atoms(model, "valid"))
    accepted = set(asp.atoms(model, "story_ok"))
    if ("p1",) not in valid or ("p1",) not in accepted:
        print("Mismatch: ASP did not accept the tribe transformation story.")
        return 1
    for params in (
        StoryParams("Luna", "Ari", "basket", seed=1),
        StoryParams("Mara", "Beko", "drum", seed=2),
    ):
        sample = generate(params)
        if not sample.story or "tribe" not in sample.story.lower():
            print("Mismatch: generated story is incomplete.")
            return 1
        if len(sample.story_qa) < 3:
            print("Mismatch: generated story lacks grounded questions.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if not params.name or not params.friend:
        raise StoryError("A tribe story needs both a main character and a friend.")

    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in f"{params.name}|{params.friend}|{params.object_name}")
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    values = {
        "name": params.name,
        "friend": params.friend,
        "object_name": params.object_name,
    }
    detail = {
        key: value.format(**values)
        for key, value in scenario.items()
        if key != "key"
    }

    world = World(params)
    protagonist = world.add(Entity(params.name, "person", params.name))
    friend = world.add(Entity(params.friend, "person", params.friend))
    tribe = world.add(Entity("tribe", "community", "the tribe"))
    object_entity = world.add(Entity("shared_object", "object", params.object_name))

    protagonist.memes.update(curiosity=1.0, patience=1.0, confidence=0.5)
    friend.memes.update(kindness=1.0, patience=1.0)
    tribe.memes.update(cooperation=1.0, belonging=1.0)
    object_entity.meters.update(before=0.3, after=1.0)

    world.facts.update(
        setting="the tribe's everyday village life",
        scenario=scenario["key"],
        transformation=True,
        problem=detail["problem"],
        clue=detail["clue"],
        safe_action=detail["action"],
        result=detail["result"],
        resolved=True,
        changed=True,
        dialogue=True,
        safe=True,
    )

    world.say(
        f"In the middle of an ordinary morning, {params.name} helped the tribe with {detail['premise']}. "
        f"The work felt familiar, but the {params.object_name} had one small surprise waiting."
    )
    world.say(
        f"{detail['problem']}. {params.name} touched the {params.object_name} carefully and looked at {params.friend}. "
        f"Neither friend hurried to blame the object."
    )
    world.say(
        f"They watched for a moment and found the clue: {detail['clue']}. "
        f"{detail['dialogue']}"
    )
    world.say(
        f"The two friends told the nearby tribe members what they had noticed. "
        f"{detail['action']}. Everyone took a calm turn, and the work became quieter."
    )
    world.say(
        f"Little by little, the change appeared: {detail['result']}. "
        f"{params.name} smiled because {detail['lesson']}."
    )
    world.say(
        f"{detail['ending']}. The tribe returned to its ordinary day, carrying the new shape of the moment with them."
    )

    story_qa = [
        QAItem(
            question=f"What problem did {params.name} notice?",
            answer=f"{params.name} noticed that {detail['problem']}.",
        ),
        QAItem(
            question="What clue helped the friends understand the problem?",
            answer=f"The clue was that {detail['clue']}.",
        ),
        QAItem(
            question="What did the tribe do to transform the situation?",
            answer=f"The tribe helped as the friends {detail['action'].lower()}.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, {detail['result']}.",
        ),
        QAItem(
            question="What lesson did the ordinary moment teach?",
            answer=f"It taught that {detail['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a tribe?",
            answer="A tribe is a community of people connected by shared life, care, traditions, or cooperation.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a meaningful change in shape, condition, understanding, or behavior.",
        ),
        QAItem(
            question="Why can everyday work matter in a story?",
            answer="Everyday work matters because small choices can reveal kindness, cooperation, and important changes.",
        ),
    ]
    prompts = [
        f"Tell a slice-of-life story about {params.name} helping a tribe transform a {params.object_name}.",
        f"Write a gentle tribe story where {params.name} and {params.friend} notice a small problem and solve it together.",
        "Show a transformation through ordinary work, dialogue, cooperation, and a concrete ending image.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(aspire())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Ari", "basket", seed=base_seed),
            StoryParams("Mara", "Beko", "drum", seed=base_seed + 1),
            StoryParams("Tavi", "Cora", "clay cup", seed=base_seed + 2),
            StoryParams("Niko", "Danu", "garden gate", seed=base_seed + 3),
        ]
    else:
        params_list = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
