#!/usr/bin/env python3
"""
A heartwarming little storyworld about sharing a strange word, repeating it
until everyone understands, and finding friendship in a tiny language puzzle.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


WORD_CHOICES = ["hypothetical", "loll", "hyphen"]
HERO_NAMES = ["Luna", "Mara", "Theo", "Ivy", "Niko", "Sana"]
HELPER_NAMES = ["Ari", "Bea", "Milo", "June", "Owen", "Tess"]
PLACES = ["a sunny reading corner", "a little library table", "the cozy word garden", "a window seat"]
OBJECTS = ["a paper star", "a blue bookmark", "a red story card", "a folded paper moon"]


@dataclass
class StoryParams:
    word: str
    hero: str
    helper: str
    place: str
    object_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


@dataclass(frozen=True)
class Arc:
    object_action: str
    trouble: str
    mistaken: str
    clue: str
    helper_line: str
    hero_line: str
    shared_action: str
    change: str
    ending: str
    joke: str


ARCS = [
    Arc(
        "write the word on a paper star",
        "the long word spilled across the star and left no room for the drawing",
        "the star was simply too small to hold a big idea",
        "the word could be split into friendly parts without losing its meaning",
        "'Maybe we can make space by sharing the word one piece at a time.'",
        "'Hypothetical,' said Luna slowly. 'It means we are imagining what might happen.'",
        "took turns saying the word and explaining one small part",
        "the word stopped feeling like a wall and became a bridge",
        "a whole row of children repeated the word together, then added their own imaginary ideas",
        "The paper star looked as if it had learned a very large dance.",
    ),
    Arc(
        "place the word beside a stack of story cards",
        "the cards kept sliding apart whenever the word was read aloud",
        "the cards were being naughty because they did not like the word",
        "a hyphen could gently join two ideas when a word needed a little hand to hold",
        "'The cards are not naughty. They may just need a joining mark.'",
        "'A hyphen is a tiny bridge,' Luna answered. 'It helps words stay together.'",
        "shared the cards and repeated the joined phrases in a steady rhythm",
        "everyone learned that small marks can help big thoughts travel",
        "the cards formed a neat path from one reader to the next",
        "The hyphen was so small that everyone agreed it must be a very quiet helper.",
    ),
    Arc(
        "draw a smiling face beside the word",
        "the new word made one child giggle while another child stayed very quiet",
        "the giggle meant that someone was laughing at somebody",
        "a gentle laugh can be shared when everyone knows the joke is kind",
        "'We can loll together, but first we should make sure every heart feels safe.'",
        "'Loll means to laugh softly,' Luna said. 'Let us invite, not tease.'",
        "shared the joke, repeated it kindly, and left room for a quiet smile",
        "the laugh became a welcome instead of a lonely sound",
        "even the quiet child added a tiny loll, and the group made space for it",
        "The smile traveled around the table like a warm little sun.",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming sharing-and-repetition word storyworld.")
    parser.add_argument("--word", choices=WORD_CHOICES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", choices=OBJECTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    word = args.word or rng.choice(WORD_CHOICES)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    place = args.place or rng.choice(PLACES)
    object_name = args.object_name or rng.choice(OBJECTS)
    if hero == helper:
        raise StoryError("hero and helper must be different characters")
    return StoryParams(word, hero, helper, place, object_name)


def build_world(params: StoryParams) -> World:
    if params.word not in WORD_CHOICES:
        raise StoryError(f"unsupported word: {params.word}")
    world = World(params)
    world.add(Entity("hero", "character", params.hero, "child", memes={"warmth": 1.0}))
    world.add(Entity("helper", "character", params.helper, "child", memes={"kindness": 1.0}))
    world.add(Entity("word", "thing", params.word, "word", meters={"shared_turns": 0.0}, memes={"belonging": 0.0}))
    world.add(Entity("keepsake", "thing", params.object_name, "paper_object", meters={"space": 1.0}))
    return world


def choose_arc(params: StoryParams) -> Arc:
    return ARCS[WORD_CHOICES.index(params.word)]


def generate_story(world: World) -> None:
    p = world.params
    arc = choose_arc(p)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    word = world.entities["word"]

    world.say(
        f"In {p.place}, {p.hero} found {p.object_name} and wanted to share a new word with {p.helper}."
    )
    world.say(
        f"The word was '{p.word}', a curious word that seemed to carry a whole pocketful of meaning. "
        f"{p.hero} began to {arc.object_action}."
    )
    world.para()

    world.say(f"Then {arc.trouble}.")
    world.say(f"{p.hero} wondered whether {arc.mistaken}.")
    world.say(f"{p.helper} looked closely and said, \"{arc.helper_line}\"")
    world.say(f"{p.hero} listened, then replied, \"{arc.hero_line}\"")
    world.facts["trouble"] = arc.trouble
    world.facts["mistaken"] = arc.mistaken
    world.facts["clue"] = arc.clue
    hero.memes["worried"] = 1.0
    helper.memes["helpful"] = 2.0

    world.para()
    world.say(f"They tested the idea by noticing that {arc.clue}.")
    world.say(f"Together, they {arc.shared_action}.")
    world.say(
        f"First they said '{p.word}' softly. Then they said it again, a little more bravely. "
        f"On the third repetition, the word felt ready to belong to everyone."
    )
    world.say(f"{p.helper} smiled. \"{arc.change.capitalize()}.\"")
    world.say(f"{p.hero} laughed gently. {arc.joke}")
    word.meters["shared_turns"] = 3.0
    word.memes["belonging"] = 2.0
    hero.memes["worried"] = 0.0
    hero.memes["proud"] = 1.0
    helper.memes["joy"] = 2.0

    world.para()
    world.say(
        f"After that, {p.hero} and {p.helper} invited the other children to share the word too. "
        f"Each child repeated it once and added a small thought of their own."
    )
    world.say(f"{arc.ending}.")
    world.say(
        f"When the activity ended, {p.object_name} rested between {p.hero} and {p.helper}, "
        f"covered with shared words and warm, careful smiles."
    )
    world.facts.update(
        {
            "word": p.word,
            "sharing": True,
            "repetition": True,
            "resolution": arc.change,
            "ending": arc.ending,
            "complete": True,
        }
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    p = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a heartwarming story in {p.place} about {p.hero} sharing the word '{p.word}' with {p.helper}.",
            f"Show repetition as {p.hero} and {p.helper} say '{p.word}' until everyone feels included.",
            f"Use the words hypothetical, loll, and hyphen in a gentle story about sharing language.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            f"What word did {p.hero} share with {p.helper}?",
            f"{p.hero} shared the word '{p.word}' with {p.helper}. They repeated it together so its meaning could feel friendly and clear.",
        ),
        QAItem(
            f"What problem happened with {p.object_name}?",
            f"{world.facts['trouble'].capitalize()} At first, {p.hero} wondered whether {world.facts['mistaken']}.",
        ),
        QAItem(
            f"How did {p.hero} and {p.helper} solve the problem?",
            f"They noticed that {world.facts['clue']}, then shared the word by taking turns saying it and explaining it kindly.",
        ),
        QAItem(
            f"What changed by the end of the story?",
            f"The word '{p.word}' became something everyone could share. {world.facts['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is sharing?",
            "Sharing means letting other people take part in something, such as an idea, a turn, a toy, or a story.",
        ),
        QAItem(
            "Why can repetition help someone learn?",
            "Repetition gives a person more chances to hear, remember, and understand something.",
        ),
        QAItem(
            "What is a hyphen?",
            "A hyphen is a short mark that can join parts of a word or connect words in a phrase.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("word", word) for word in WORD_CHOICES]
    lines.extend(
        [
            asp.fact("feature", "sharing"),
            asp.fact("feature", "repetition"),
            asp.fact("style", "heartwarming"),
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
story_word(W) :- word(W).
has_sharing(W) :- story_word(W), feature(sharing).
has_repetition(W) :- story_word(W), feature(repetition).
heartwarming(W) :- story_word(W), style(heartwarming).
complete(W) :- has_sharing(W), has_repetition(W), heartwarming(W).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(
        asp_program(
            "#show story_word/1.\n#show has_sharing/1.\n#show has_repetition/1.\n#show heartwarming/1.\n#show complete/1."
        )
    )
    expected = {(word,) for word in WORD_CHOICES}
    checks = {
        "story_word": set(asp.atoms(model, "story_word")),
        "has_sharing": set(asp.atoms(model, "has_sharing")),
        "has_repetition": set(asp.atoms(model, "has_repetition")),
        "heartwarming": set(asp.atoms(model, "heartwarming")),
        "complete": set(asp.atoms(model, "complete")),
    }
    if all(value == expected for value in checks.values()):
        for seed in (3, 17, 91):
            sample = generate(
                StoryParams(
                    word=WORD_CHOICES[seed % len(WORD_CHOICES)],
                    hero="Luna",
                    helper="Ari",
                    place=PLACES[seed % len(PLACES)],
                    object_name=OBJECTS[seed % len(OBJECTS)],
                    seed=seed,
                )
            )
            if not sample.story or "shared" not in sample.story.lower():
                print("Generated-story verification failed.")
                return 1
        print("OK: ASP parity and generated-story checks passed.")
        return 0
    print("Mismatch between ASP and Python registries.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"P{index}: {prompt}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams("hypothetical", "Luna", "Ari", PLACES[0], OBJECTS[0]),
    StoryParams("loll", "Mara", "Bea", PLACES[1], OBJECTS[1]),
    StoryParams("hyphen", "Theo", "June", PLACES[2], OBJECTS[2]),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_word/1.\n#show complete/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show story_word/1.\n#show complete/1."))
        print(f"story_word={len(asp.atoms(model, 'story_word'))}")
        print(f"complete={len(asp.atoms(model, 'complete'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(100, args.n * 30):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
            header = f"### {sample.params.hero} shares '{sample.params.word}'"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
