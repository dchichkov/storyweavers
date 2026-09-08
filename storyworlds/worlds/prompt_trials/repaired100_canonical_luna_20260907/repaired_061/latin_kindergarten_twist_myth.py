#!/usr/bin/env python3
"""
A gentle kindergarten myth about Luna, a Latin word, and a twist that turns
a quiet classroom problem into a shared discovery.
"""

from __future__ import annotations

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
    place: str = "kindergarten"
    child: str = "Luna"
    helper: str = "Mateo"
    latin_word: str = "lumen"
    object_name: str = "a little clay sun"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    seen_twist: bool = False
    resolved: bool = False

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


LATIN_WORDS = {
    "lumen": ("light", "A light can help us see."),
    "amicus": ("friend", "A friend is someone who cares and helps."),
    "terra": ("earth", "Earth is the ground beneath our feet."),
    "aqua": ("water", "Water helps living things grow."),
    "cor": ("heart", "A heart helps us feel care and courage."),
    "luna": ("moon", "The moon shines above the sleeping world."),
}

CHILDREN = ["Luna", "Mateo", "Sofia", "Noah", "Mina", "Theo"]
OBJECTS = [
    "a little clay sun",
    "a paper moon",
    "a painted wooden star",
    "a blue ribbon crown",
]
TWISTS = [
    {
        "opening": "On Monday morning, Luna found a golden mark beneath the reading rug.",
        "problem": "The mark seemed to point toward the class word card, but the card had vanished.",
        "guess": "Maybe the word flew away because it was lonely.",
        "clue": "a trail of yellow dust leading from the rug to the art shelf",
        "turn": "The missing card was not lost at all: it had been tucked inside a paper lantern by the class puppet.",
        "meaning": "The puppet had copied the Latin word because it wanted to learn what the children were learning.",
        "ending": "The lantern glowed above the circle, and the new word card rested safely beside it.",
    },
    {
        "opening": "Before story time, Luna heard a tiny bell ring inside the kindergarten cupboard.",
        "problem": "Every time she opened the door, the bell stopped and a paper star slid farther into the darkness.",
        "guess": "A small sky spirit must be hiding in there.",
        "clue": "blue paint on the cupboard handle and a line of crumbs beneath it",
        "turn": "The sound came from a wind-up bell hidden in the puppet basket, where Mateo had placed the star for a surprise.",
        "meaning": "Mateo had made a secret word hunt, but the first clue had slipped into the wrong basket.",
        "ending": "The bell rang once more as the children placed the star above the word table.",
    },
    {
        "opening": "Luna brought a smooth stone to kindergarten and set it beside the Latin word card.",
        "problem": "At noon, the stone appeared on the other side of the room beside the class plant.",
        "guess": "The stone is walking like an ancient giant.",
        "clue": "a damp crescent on the floor and a leaf bent toward the window",
        "turn": "The stone had been carried by the class snail, who had hidden beneath it after a gentle watering.",
        "meaning": "The snail had moved the stone toward the plant because the stone was warm and dry.",
        "ending": "The stone became the snail's safe bridge while the children whispered the new word together.",
    },
    {
        "opening": "A silver thread appeared across the kindergarten floor before the children arrived.",
        "problem": "It led to an empty chair where Luna's clay sun had been sitting.",
        "guess": "The sun has followed a thread into the clouds.",
        "clue": "small bits of yellow clay beside the block shelf",
        "turn": "The clay sun had rolled away during cleanup and stopped inside a block castle.",
        "meaning": "The children had built the castle around it without noticing, making a tiny temple for their classroom sun.",
        "ending": "The clay sun stood on the castle tower while the class greeted it with a bright new word.",
    },
]

def build_world(params: StoryParams) -> World:
    if params.latin_word not in LATIN_WORDS:
        raise StoryError(f"unknown Latin word: {params.latin_word}")
    if params.child == params.helper:
        raise StoryError("the child and helper must be different children")
    w = World(params)
    child = w.add(Entity("child", "character", "kindergartner", params.child))
    helper = w.add(Entity("helper", "character", "kindergartner", params.helper))
    word = w.add(Entity("word", "thing", "latin_word", params.latin_word))
    object_entity = w.add(Entity("object", "thing", "classroom_object", params.object_name))
    child.memes.update(curiosity=1.0, courage=0.0, wonder=0.0)
    helper.memes.update(kindness=1.0, teamwork=0.0)
    word.meters["meaning"] = 1.0
    w.facts["child"] = child
    w.facts["helper"] = helper
    w.facts["word"] = word
    w.facts["object"] = object_entity
    index = (params.seed or 0) % len(TWISTS)
    w.facts["twist"] = TWISTS[index]
    w.facts["twist_index"] = index
    return w


def narrate(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    word: Entity = world.facts["word"]  # type: ignore[assignment]
    obj: Entity = world.facts["object"]  # type: ignore[assignment]
    twist: dict[str, str] = world.facts["twist"]  # type: ignore[assignment]
    meaning, explanation = LATIN_WORDS[p.latin_word]

    world.say(f"In the little {p.place}, {twist['opening']}")
    world.say(f"{child.label} carried {obj.label} to the circle, where the class was learning the Latin word {p.latin_word}.")
    world.say(f'"What does {p.latin_word} mean?" asked {child.label}. "{meaning.capitalize()}," said {helper.label}, reading the card.')

    world.para()
    child.memes["wonder"] = 1.0
    world.say(twist["problem"])
    world.say(f'"{twist["guess"]}" whispered {child.label}. {helper.label} shook their head gently. "Let us look for a real clue."')
    world.say(f"Together they noticed {twist['clue']}. The clue made the room feel like an old myth waiting to be told.")

    world.para()
    world.seen_twist = True
    child.memes["courage"] = 1.0
    helper.memes["teamwork"] = 1.0
    world.say(f"They followed the clue carefully, and then came the twist: {twist['turn']}")
    world.say(f'"I thought the mystery was magic," said {child.label}. "It was kindness and careful noticing," replied {helper.label}. {twist["meaning"]}')

    world.para()
    world.resolved = True
    child.meters["understanding"] = 1.0
    word.meters["shared"] = 1.0
    world.say(f"The children placed {obj.label} beside the Latin word card and said, "{p.latin_word}!" together.")
    world.say(f"{explanation} {twist['ending']} By nap time, the kindergarten felt like a small bright temple of questions, friendship, and learning.")


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle myth-like kindergarten story about {p.child}, a Latin word, and a surprising twist.",
        f"Tell a child-facing story in a kindergarten where {p.child} and {p.helper} solve a classroom mystery through dialogue.",
        f"Create a short myth about the Latin word {p.latin_word}, with a clue, a twist, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    twist: dict[str, str] = world.facts["twist"]  # type: ignore[assignment]
    meaning, _ = LATIN_WORDS[p.latin_word]
    return [
        QAItem(
            question=f"Where did {p.child} and {p.helper} solve their mystery?",
            answer=f"They solved it together in their kindergarten classroom.",
        ),
        QAItem(
            question=f"What Latin word were the children learning?",
            answer=f"They were learning the Latin word {p.latin_word}, which means {meaning}.",
        ),
        QAItem(
            question=f"What clue helped the children?",
            answer=f"The clue was {twist['clue']}. It showed them where to look next.",
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer=f"The twist was that {twist['turn']}",
        ),
        QAItem(
            question=f"How did {p.child} and {p.helper} solve the problem?",
            answer=f"They talked together, searched carefully, and used the clue instead of trusting their first guess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    meaning, explanation = LATIN_WORDS[p.latin_word]
    return [
        QAItem(
            question="What is a myth-like story?",
            answer="A myth-like story is a tale with wonder, symbolic events, and a lesson about how people live together.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising change that makes the reader understand the problem in a new way.",
        ),
        QAItem(
            question=f"What does the Latin word {p.latin_word} mean?",
            answer=f"The Latin word {p.latin_word} means {meaning}. {explanation}",
        ),
        QAItem(
            question="Why is dialogue useful in a story?",
            answer="Dialogue lets characters share ideas, correct guesses, and change what they decide to do.",
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
    lines.append(f"latin_word={world.params.latin_word}")
    lines.append(f"twist={world.seen_twist} resolved={world.resolved}")
    return "\n".join(lines)


ASP_RULES = r"""
character(X) :- child(X).
character(X) :- helper(X).
has_clue :- clue(_).
has_dialogue :- speaks(_,_).
has_twist :- reveal(_).
resolved :- has_clue, has_dialogue, has_twist.
#show resolved/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for child in CHILDREN:
        lines.append(asp.fact("child", child.lower()))
    for word in LATIN_WORDS:
        lines.append(asp.fact("latin_word", word))
    lines.append(asp.fact("clue", "observed"))
    lines.append(asp.fact("speaks", "child", "helper"))
    lines.append(asp.fact("reveal", "twist"))
    return "\n".join(lines)


def asp_program(show: str = "#show resolved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    asp_ok = any(sym.name == "resolved" for sym in model)
    params = StoryParams(seed=17)
    sample = generate(params)
    py_ok = sample.world is not None and sample.world.seen_twist and sample.world.resolved
    if asp_ok and py_ok:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Kindergarten myth storyworld about Latin, friendship, and a twist."
    )
    parser.add_argument("--place", choices=["kindergarten"])
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--helper", choices=CHILDREN)
    parser.add_argument("--latin-word", choices=sorted(LATIN_WORDS))
    parser.add_argument("--object-name", choices=OBJECTS)
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


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    child = args.child or rng.choice(CHILDREN)
    possible_helpers = [name for name in CHILDREN if name != child]
    helper = args.helper or rng.choice(possible_helpers)
    return StoryParams(
        place=args.place or "kindergarten",
        child=child,
        helper=helper,
        latin_word=args.latin_word or rng.choice(list(LATIN_WORDS)),
        object_name=args.object_name or rng.choice(OBJECTS),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
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
        combinations = [
            ("Luna", "Mateo", "lumen", "a little clay sun"),
            ("Sofia", "Noah", "amicus", "a paper moon"),
            ("Mina", "Theo", "terra", "a painted wooden star"),
            ("Theo", "Luna", "cor", "a blue ribbon crown"),
        ]
        samples = [
            generate(
                StoryParams(
                    place="kindergarten",
                    child=child,
                    helper=helper,
                    latin_word=word,
                    object_name=obj,
                    seed=base_seed + i,
                )
            )
            for i, (child, helper, word, obj) in enumerate(combinations)
        ]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 10):
            attempts += 1
            sample_seed = base_seed + attempts
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            if params.child == params.helper:
                raise StoryError("the child and helper must be different children")
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if not samples:
        raise StoryError("no stories could be generated")

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
