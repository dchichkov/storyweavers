#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a magical book, a careful explosion,
and a reconciliation that turns a bitter secret into a new beginning.
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
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    kingdom: str = "Moonvale"
    reader: str = "Luna"
    rival: str = "Mira"
    book: str = "The Book of Unfinished Stars"
    powder: str = "stardust"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.exploded = False
        self.reconciled = False
        self.twist_revealed = False

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


KINGDOMS = ["Moonvale", "Rosemere", "Thornhaven", "Silverfen"]
READERS = ["Luna", "Elio", "Nera", "Pip"]
RIVALS = ["Mira", "Corin", "Tavi", "Bram"]
BOOKS = [
    "The Book of Unfinished Stars",
    "The Golden Grammar",
    "The Library Beneath the Lake",
    "The Tale of the Clockwork Dragon",
]
POWDERS = ["stardust", "dragon-salt", "sunflower ash", "blue comet dust"]

TALES = [
    {
        "opening": "In the oldest tower of the kingdom stood a library where every book whispered when the moon rose.",
        "problem": "One night, the final page of the kingdom's most precious literature vanished from its book.",
        "accusation": "Mira must have stolen it to win the royal storytelling contest.",
        "clue": "a silver ink stain beneath the library window",
        "method": "Luna placed the book inside a circle of salt and read the backward letters aloud.",
        "twist": "the missing page had not been stolen at all; it had hidden itself because the ending made two friends quarrel forever",
        "memory": "the girls had once promised to write every story together, but each had secretly feared the other was the better writer",
        "ending": "They wrote a new ending in which the two heroes shared the crown, and the library bells sang until dawn.",
    },
    {
        "opening": "Beyond the rose gate of the kingdom, a fairy library grew from the roots of one enormous tree.",
        "problem": "A locked volume began to shake whenever Luna opened a different story.",
        "accusation": "Mira had cursed the book because she was jealous of Luna's bright imagination.",
        "clue": "two sets of footprints circled the same reading stool",
        "method": "Luna asked Mira to hold the key while she turned the pages slowly.",
        "twist": "the book was shaking because it contained both girls' unfinished wishes, pressed together like two wings",
        "memory": "Mira had saved Luna's first story years before, while Luna had forgotten to thank her",
        "ending": "The girls finished the book side by side, and its tree grew a new branch shaped like a heart.",
    },
    {
        "opening": "At midnight, the royal library floated above the clouds on a bridge of moonlight.",
        "problem": "A black mark spread across a beloved fairy tale, threatening to erase every happy ending.",
        "accusation": "Mira had brought the darkness to punish Luna for keeping the best tales to herself.",
        "clue": "the mark stopped wherever two readers spoke kindly to one another",
        "method": "Luna and Mira read the story aloud together and sprinkled powder over the dark letters.",
        "twist": "the darkness was a lonely ink-spirit, born from all the words that readers had refused to say",
        "memory": "both girls had been waiting for the other to apologize first",
        "ending": "The ink-spirit became a small black bird and carried their apology from shelf to shelf.",
    },
    {
        "opening": "The queen kept a palace of books, and each volume had a tiny door for a fairy to enter.",
        "problem": "When Luna opened her favorite volume, its pages began to explode into harmless golden feathers.",
        "accusation": "Mira had tampered with the book to embarrass Luna before the queen.",
        "clue": "a hidden bookmark bore both girls' initials",
        "method": "Luna closed the cover halfway and invited Mira to explain what she remembered.",
        "twist": "the book had been enchanted by their younger selves, who had hidden a promise inside it",
        "memory": "the promise said that neither girl should ever let pride make her write alone",
        "ending": "The golden feathers settled into a new cover, and the queen named them royal keepers of literature.",
    },
]


def build_world(params: StoryParams) -> World:
    world = World(params)
    reader = world.add(
        Entity(
            id="reader",
            kind="character",
            type="girl",
            label=params.reader,
            meters={"courage": 0.4, "trust": 0.2},
            memes={"curiosity": 1.0, "hurt": 0.5},
        )
    )
    rival = world.add(
        Entity(
            id="rival",
            kind="character",
            type="girl",
            label=params.rival,
            meters={"courage": 0.3, "trust": 0.1},
            memes={"jealousy": 0.4, "hurt": 0.6},
        )
    )
    book = world.add(
        Entity(
            id="book",
            kind="thing",
            type="literature",
            label=params.book,
            meters={"pages": 100.0, "danger": 0.4},
            memes={"memory": 1.0},
        )
    )
    world.add(
        Entity(
            id="powder",
            kind="thing",
            type="magic",
            label=params.powder,
            meters={"brightness": 0.8},
            memes={"calm": 1.0},
        )
    )
    index = (params.seed or 0) % len(TALES)
    world.facts.update(
        reader=reader,
        rival=rival,
        book=book,
        tale=TALES[index],
        tale_index=index,
    )
    return world


def narrate(world: World) -> None:
    p = world.params
    reader: Entity = world.facts["reader"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    book: Entity = world.facts["book"]  # type: ignore[assignment]
    tale: dict[str, str] = world.facts["tale"]  # type: ignore[assignment]

    world.say(
        f"{tale['opening']} In {p.kingdom}, {reader.label} loved literature so dearly "
        f"that she could hear a story sigh before anyone else."
    )
    world.say(
        f"Her friend {rival.label} loved the same books, but lately they had stopped reading together. "
        f"That evening, {reader.label} found {book.label} trembling on its stand."
    )
    world.say(
        f'"Did you touch it?" asked {reader.label}. "{rival.label} did," whispered a page, '
        f'"but not in the way you think."'
    )

    world.para()
    world.say(tale["problem"])
    reader.memes["fear"] = 0.8
    rival.memes["fear"] = 0.7
    world.say(
        f'{reader.label} pointed at {rival.label}. "{tale["accusation"]}" '
        f'{rival.label} stepped back. "You always think the worst of me."'
    )
    world.say(
        f'Then {reader.label} noticed {tale["clue"]}. The clue made her pause before anger could explode.'
    )

    world.para()
    world.say(
        f'"Let us learn the truth together," said {reader.label}. '
        f'"Will you help me?" {rival.label} looked surprised. "Yes, if you will listen."'
    )
    world.say(tale["method"])
    world.exploded = True
    book.meters["danger"] = 0.1
    world.say(
        f'The magic did not roar. Instead, the {p.powder} began to glow, and then the book did explode '
        f'into a fountain of harmless stars.'
    )

    world.para()
    world.twist_revealed = True
    world.say(f'Among the stars came the twist: {tale["twist"]}.')
    world.say(
        f'The book showed them a memory: {tale["memory"]}. '
        f'{reader.label} lowered her eyes. "{rival.label}, I am sorry I blamed you." '
        f'{rival.label} answered, "I am sorry I hid the clue from you."'
    )
    reader.memes["hurt"] = 0.0
    rival.memes["hurt"] = 0.0
    reader.meters["trust"] = 1.0
    rival.meters["trust"] = 1.0
    world.reconciled = True

    world.para()
    world.say(
        f'Together they repaired {book.label} with a thread of moonlight and wrote a kinder ending. '
        f'{tale["ending"]}'
    )
    world.say(
        f'From that night on, {reader.label} and {rival.label} shared every story, '
        f'and no secret was ever allowed to grow larger than a friendship.' 
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a fairy tale about {p.reader} and {p.rival} using magical literature, an explosion, a twist, and reconciliation.",
        f"Tell a child-friendly story in {p.kingdom} where a book seems dangerous but helps two friends forgive one another.",
        f"Create a fairy tale in which {p.book} explodes into magic and reveals why two friends must reconcile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    reader: Entity = world.facts["reader"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    book: Entity = world.facts["book"]  # type: ignore[assignment]
    tale: dict[str, str] = world.facts["tale"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What kind of literature caused trouble for {reader.label} and {rival.label}?",
            answer=f"The magical literature was {book.label}, a book whose pages held an unfinished secret.",
        ),
        QAItem(
            question=f"What did {reader.label} first accuse {rival.label} of doing?",
            answer=f"{reader.label} first accused {rival.label} of stealing or harming the missing part of the book, but the clue showed that this guess was unfair.",
        ),
        QAItem(
            question=f"What happened when the magic was used on {book.label}?",
            answer=f"The book exploded into harmless golden stars, and the magical display revealed the truth hidden inside its pages.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {tale['twist']}. The mystery came from hurt feelings rather than from a wicked thief.",
        ),
        QAItem(
            question=f"How did {reader.label} and {rival.label} reconcile?",
            answer=f"They listened to each other, apologized for blaming and hiding things, and repaired the book together with moonlight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is literature?",
            answer="Literature is writing such as stories, poems, and plays that can entertain people or help them understand ideas and feelings.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change or discovery that makes earlier events look different.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a relationship after people have argued or hurt one another.",
        ),
        QAItem(
            question="Why can an explosion in a fairy tale be safe?",
            answer="A fairy-tale explosion can be magical and harmless when the story clearly shows that it creates wonder instead of injury.",
        ),
        QAItem(
            question=f"What is {p.kingdom} in this story?",
            answer=f"{p.kingdom} is the enchanted kingdom where the magical library and its talking literature are found.",
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
    lines.append(f"tale={world.facts['tale_index']}")
    lines.append(
        f"exploded={world.exploded} twist_revealed={world.twist_revealed} reconciled={world.reconciled}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
literature(B) :- book(B).
dangerous(B) :- book(B), missing_page(B).
magic_used(B) :- book(B), powder(B).
exploded(B) :- magic_used(B).
twist :- exploded(B), hidden_truth(B).
reconciled :- apology(reader, rival), apology(rival, reader).
good_story :- literature(B), exploded(B), twist, reconciled.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for book in BOOKS:
        lines.append(asp.fact("book", book))
    for powder in POWDERS:
        lines.append(asp.fact("powder", powder))
    lines.extend(
        [
            asp.fact("missing_page", BOOKS[0]),
            asp.fact("reader", "reader"),
            asp.fact("rival", "rival"),
            asp.fact("magic_used", BOOKS[0]),
            asp.fact("hidden_truth", BOOKS[0]),
            asp.fact("apology", "reader", "rival"),
            asp.fact("apology", "rival", "reader"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_story/0."))
    asp_good = any(symbol.name == "good_story" for symbol in model)
    python_good = True
    if asp_good != python_good:
        print("MISMATCH between ASP and Python.")
        return 1

    for seed in range(8):
        sample = generate(
            StoryParams(
                kingdom=KINGDOMS[seed % len(KINGDOMS)],
                reader=READERS[seed % len(READERS)],
                rival=RIVALS[seed % len(RIVALS)],
                book=BOOKS[seed % len(BOOKS)],
                powder=POWDERS[seed % len(POWDERS)],
                seed=seed,
            )
        )
        if not all(
            word in sample.story.lower()
            for word in ("literature", "explode", "twist", "sorry")
        ):
            print("Generated story verification failed.")
            return 1
    print("OK: ASP and Python parity verified; generated stories exercised.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale literature storyworld with an explosion, twist, and reconciliation."
    )
    parser.add_argument("--kingdom", choices=KINGDOMS)
    parser.add_argument("--reader", choices=READERS)
    parser.add_argument("--rival", choices=RIVALS)
    parser.add_argument("--book", choices=BOOKS)
    parser.add_argument("--powder", choices=POWDERS)
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
    reader = args.reader or rng.choice(READERS)
    rival = args.rival or rng.choice([name for name in RIVALS if name != reader])
    return StoryParams(
        kingdom=args.kingdom or rng.choice(KINGDOMS),
        reader=reader,
        rival=rival,
        book=args.book or rng.choice(BOOKS),
        powder=args.powder or rng.choice(POWDERS),
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.reader == params.rival:
        raise StoryError("reader and rival must be different characters")
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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combinations = [
            ("Moonvale", "Luna", "Mira", BOOKS[0], POWDERS[0]),
            ("Rosemere", "Elio", "Corin", BOOKS[1], POWDERS[1]),
            ("Thornhaven", "Nera", "Tavi", BOOKS[2], POWDERS[2]),
            ("Silverfen", "Pip", "Bram", BOOKS[3], POWDERS[3]),
        ]
        for index, values in enumerate(combinations):
            samples.append(generate(StoryParams(*values, seed=base_seed + index)))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 10):
            attempts += 1
            sample_seed = base_seed + attempts
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            sample = generate(params)
            if sample.story in seen:
                continue
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
