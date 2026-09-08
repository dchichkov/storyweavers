#!/usr/bin/env python3
"""
A gentle fable about a bee whose quest transforms a proud value into useful
kindness.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the meadow"
    hero: str = "Bina"
    helper: str = "the old tortoise"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the meadow": {"plants": "clover and daisies", "mood": "bright and breezy"},
    "the orchard": {"plants": "apple blossoms", "mood": "sweet and golden"},
    "the garden": {"plants": "roses and lavender", "mood": "fragrant and quiet"},
}


@dataclass(frozen=True)
class QuestArc:
    title: str
    premise: str
    trouble: str
    conversation: str
    action: str
    transformation: str
    ending: str
    trouble_answer: str
    value_answer: str
    transformation_answer: str


ARCS = [
    QuestArc(
        "The Bee Who Counted Her Honey",
        "Bina counted every drop of honey and believed that having the most made her the most important bee.",
        "Then a dry wind bent the flowers, and the hive's youngest bees found no sweet food for the night.",
        'The tortoise asked, "What good is a full jar if your neighbors have empty cups?" Bina replied, "I had not thought of honey that way."',
        "Bina opened her store and led the bees to the last patch of clover, where they gathered only what the flowers could spare.",
        "Her value changed from keeping the most to helping the whole hive endure.",
        "At sunset, Bina watched many small cups shine beside her own.",
        "A dry wind left the young bees without enough food.",
        "Bina learned that generosity matters more than possessing the largest store.",
        "She shared her honey and guided the hive to flowers without harming the plants.",
    ),
    QuestArc(
        "The Long Flight for One Flower",
        "Bina prized speed and boasted that no bee could fly farther or faster than she could.",
        "A tiny blue flower grew beyond a muddy stream, but an old bee could not reach its nectar to make medicine.",
        'The tortoise said, "A fast wing is useful, but a patient wing can carry a friend." Bina answered, "Then I will slow down enough to help."',
        "Bina carried the old bee across the stream, rested when asked, and returned with the flower's healing nectar.",
        "Her pride in speed transformed into respect for patient teamwork.",
        "The old bee sipped the medicine while Bina flew beside her at a gentle pace.",
        "An old bee needed nectar from a flower beyond a dangerous stream.",
        "Bina chose to use her speed for another bee instead of boasting about it.",
        "Helping the old bee transformed Bina's pride into patient teamwork.",
    ),
    QuestArc(
        "The Golden Stripe",
        "Bina thought her bright golden stripe made her better than the plain brown beetles under the leaves.",
        "A sudden rain flooded the beetles' shelter, and the little creatures had nowhere dry to stand.",
        'The tortoise asked, "Does a stripe make a shelter?" Bina looked at the rain and said, "No, but my wings can help build one."',
        "Bina gathered broad leaves, while the beetles pushed twigs into place and the tortoise held the roof steady.",
        "Her wish to appear special transformed into a wish to make room for others.",
        "When the rain stopped, the golden stripe was seen beneath a wide leaf roof shared by every small creature.",
        "Rain flooded the beetles' shelter.",
        "Bina discovered that her appearance could not help anyone, but her wings and effort could.",
        "Working with the beetles and tortoise built a safe shared shelter.",
    ),
    QuestArc(
        "The Quiet Buzz",
        "Bina believed the loudest buzz always won the hive's attention.",
        "When the queen needed to hear a warning about smoke near the flowers, every bee buzzed at once.",
        'The tortoise whispered, "A wise bee listens before she speaks." Bina answered, "I will make space for the smallest warning."',
        "Bina asked the bees to pause, and a young bee was finally heard describing a safe path through the reeds.",
        "Her hunger for attention transformed into careful listening.",
        "The hive followed the young bee's path, and Bina kept watch in a quiet flower.",
        "The hive could not hear an important warning because every bee buzzed loudly.",
        "Bina gave the youngest bee a chance to speak.",
        "Listening revealed a safe path and changed Bina's need for attention into care.",
    ),
    QuestArc(
        "The Nectar That Was Not Hers",
        "Bina found a fallen cup of nectar and decided that finding it meant owning it.",
        "A thirsty moth arrived and explained that the nectar had spilled from a flower she had been carrying home.",
        'The tortoise said, "Finding a treasure is not the same as being its owner." Bina replied, "Then I will return what I can."',
        "Bina helped the moth lift the cup and carried it back to the waiting flower.",
        "Her desire to claim a prize transformed into honesty and repair.",
        "The moth shared one small sip with Bina beside the restored flower.",
        "A moth had lost a cup of nectar that Bina wanted to keep.",
        "Bina returned the nectar after learning that it belonged to the moth.",
        "Honesty restored the flower's gift and earned Bina a grateful friend.",
    ),
]


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(
        (params.setting, params.hero, params.helper)
    )))


def fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.helper:
        raise StoryError("The bee and helper must have different names.")
    if params.setting not in SETTING_REGISTRY:
        raise StoryError("The setting must be one of the registered places.")

    number = stable_seed(params)
    arc = ARCS[number % len(ARCS)]
    world = World(params.setting)

    bee = world.add(Entity(
        params.hero,
        "bee",
        meters={"energy": 1.0, "flight": 1.0},
        memes={"pride": 1.0, "kindness": 0.0},
    ))
    helper = world.add(Entity(
        params.helper,
        "helper",
        meters={"strength": 1.0},
        memes={"wisdom": 1.0},
    ))
    world.add(Entity(
        "the flowers",
        "plants",
        meters={"nectar": 1.0},
        memes={"renewal": 1.0},
    ))
    world.add(Entity(
        "the hive",
        "home",
        meters={"shelter": 1.0},
        memes={"belonging": 1.0},
    ))

    facts = {
        "hero": params.hero,
        "helper": params.helper,
        "setting": params.setting,
        "arc": arc,
        "plants": SETTING_REGISTRY[params.setting]["plants"],
    }
    world.facts.update(facts)
    world.facts["value_before"] = "pride"
    world.facts["value_after"] = "kindness"
    world.facts["transformation"] = arc.transformation
    world.facts["quest"] = arc.title

    opening = (
        f"In {params.setting}, where {facts['plants']} grew in the "
        f"{SETTING_REGISTRY[params.setting]['mood']} air, lived a bee named "
        f"{params.hero}."
    )
    story = "\n\n".join([
        f"{opening} Her quest began when {fill(arc.premise, facts)}",
        fill(arc.trouble, facts),
        fill(arc.conversation, facts),
        fill(arc.action, facts),
        f"{fill(arc.transformation, facts)} {fill(arc.ending, facts)}",
        f"That is the lesson of {arc.title}: a moral value is not a jewel to display. "
        f"It is a seed that grows when a small creature uses it to help another.",
    ])

    prompts = [
        f"Write a fable about a bee named {params.hero} on a quest in {params.setting}.",
        "Tell a child-friendly fable in which a bee's moral value changes through a difficult task.",
        "Write a gentle transformation story about pride becoming kindness.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face in \"{arc.title}\"?",
            answer=arc.trouble_answer,
        ),
        QAItem(
            question=f"What moral value did {params.hero} learn?",
            answer=arc.value_answer,
        ),
        QAItem(
            question="How did the quest transform the bee?",
            answer=arc.transformation_answer,
        ),
        QAItem(
            question=f"How does the fable of {arc.title} end?",
            answer=f"The fable ends when {arc.ending[0].lower() + arc.ending[1:]}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a bee?",
            answer="A bee is a small flying insect that visits flowers, gathers nectar and pollen, and helps many plants make seeds.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a belief about how to act well, such as being honest, patient, generous, or kind.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change in how someone looks, thinks, feels, or behaves.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or challenge undertaken to find, fix, learn, or help.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals as characters, that teaches a lesson.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
place(meadow).
place(orchard).
place(garden).
value(pride).
value(kindness).
feature(bee).
feature(transformation).
feature(quest).
can_tell_fable(P) :- place(P), feature(bee), feature(transformation), feature(quest).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTING_REGISTRY:
        lines.append(asp.fact("place", place.replace("the ", "").replace(" ", "_")))
    for value in ("pride", "kindness"):
        lines.append(asp.fact("value", value))
    for feature in ("bee", "transformation", "quest"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bee's moral-value transformation fable.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Bina", "Meli", "Zuzu", "Pip"])
    helper = args.helper or rng.choice(["the old tortoise", "the patient robin", "the kind beetle"])
    if hero == helper:
        raise StoryError("The bee and helper must be different characters.")
    return StoryParams(setting=setting, hero=hero, helper=helper)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
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


def asp_verify() -> int:
    import asp
    python_places = {
        (place.replace("the ", "").replace(" ", "_"),)
        for place in SETTING_REGISTRY
    }
    model = asp.one_model(asp_program("#show can_tell_fable/1."))
    clingo_places = set(asp.atoms(model, "can_tell_fable"))
    if python_places == clingo_places:
        print(f"OK: clingo gate matches python ({len(python_places)} places).")
        for seed in range(8):
            sample = generate(StoryParams(seed=seed))
            if not sample.story or len(sample.story_qa) < 3:
                print("Generated-story verification failed.")
                return 1
        print("OK: generated stories passed.")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(python_places - clingo_places))
    print("clingo only:", sorted(clingo_places - python_places))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_fable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_tell_fable/1."))
        for place in sorted(asp.atoms(model, "can_tell_fable")):
            print(place[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(generate(StoryParams(
                setting=setting,
                hero="Bina",
                helper="the old tortoise",
            )))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
