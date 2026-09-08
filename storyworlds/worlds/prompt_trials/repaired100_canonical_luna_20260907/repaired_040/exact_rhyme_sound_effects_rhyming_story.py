#!/usr/bin/env python3
"""
exact_rhyme_sound_effects_rhyming_story.py

A small rhyming storyworld about an exact little bell pattern, playful sound
effects, and a careful friend who learns that a rhyme can guide a real rescue.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Pattern:
    id: str
    clue: str
    rhyme: str
    sound: str
    action: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "garden": Setting("garden", "the moonlit garden", {"rhyme_trial"}),
}

PATTERNS = {
    "bell_path": Pattern(
        "bell_path",
        "A silver bell rang beside the gate.",
        "bright / night",
        "Ding-ding! Clink-clink!",
        "followed the exact bell rhyme to find a trapped moth",
        "small clues can lead a careful heart to help",
    ),
    "pond_echo": Pattern(
        "pond_echo",
        "A pebble tapped the pond in a steady beat.",
        "plop / stop",
        "Plip-plop! Tap-tap!",
        "matched each sound and guided a duckling away from deep water",
        "listening closely can make a brave plan",
    ),
    "leaf_drum": Pattern(
        "leaf_drum",
        "A red leaf drummed beneath the old oak.",
        "tree / free",
        "Rat-a-tat! Whoosh-whee!",
        "used the exact rhythm to open a vine gate for a hedgehog",
        "a true answer is better than a hurried guess",
    ),
}

NAMES = ["Luna", "Mira", "Pip", "Nell", "Toby"]
ANIMALS = ["rabbit", "fox", "mouse", "squirrel", "badger"]
HELPERS = ["Otis", "Bram", "Tess", "Milo", "Wren"]
TRAITS = ["bright", "gentle", "curious", "brave", "thoughtful"]

OPENINGS = [
    "Luna hopped under the moon, with a tune beneath her shoe; she loved a rhyme that sounded right and told her what to do.",
    "In the garden after dark, a tiny bell began to spark; Luna heard its silver chime and set out for a rhyming time.",
    "A sleepy star looked down below while Luna watched the night flowers glow; a sound began, so clear and fine, it seemed to draw a dotted line.",
]

DIALOGUE = [
    '"Is that the exact sound?" asked {helper}. "Let us listen once again."',
    '"Ding means near and clink means right," said {helper}. "We can solve this in the night."',
    '"Do not rush the rhyme," said {helper}. "A careful ear may help us find the way."',
]

ASP_RULES = r"""
place(garden).
affords(garden,rhyme_trial).
pattern(bell_path).
pattern(pond_echo).
pattern(leaf_drum).
valid(Place,Pattern) :- place(Place), affords(Place,rhyme_trial), pattern(Pattern).
#show valid/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, pattern)
        for place, setting in SETTINGS.items()
        for pattern in PATTERNS
        if "rhyme_trial" in setting.affords
    ]


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for activity in setting.affords:
            lines.append(asp.fact("affords", place, activity))
    for pattern in PATTERNS:
        lines.append(asp.fact("pattern", pattern))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} valid combinations).")
        return 0
    print("Mismatch between Python and ASP.")
    print("Only Python:", sorted(py - clingo))
    print("Only ASP:", sorted(clingo - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a rhyming sound-effects story.")
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--pattern", choices=PATTERNS)
    parser.add_argument("--name")
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
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


@dataclass
class StoryParams:
    place: str
    pattern: str
    name: str
    animal: str
    helper: str
    trait: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.pattern is None or combo[1] == args.pattern
    ]
    if not combos:
        raise StoryError("No valid place and pattern combination matches those choices.")
    place, pattern = rng.choice(combos)
    return StoryParams(
        place=place,
        pattern=pattern,
        name=args.name or rng.choice(NAMES),
        animal=args.animal or rng.choice(ANIMALS),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    pattern = PATTERNS[params.pattern]
    world = World(setting)
    hero = world.add(Entity(params.name, type=params.animal, label=params.trait))
    helper = world.add(Entity(params.helper, type="songbird", label="helper"))
    world.add(Entity("moth", type="moth", label="small listener"))

    rng = random.Random(params.seed if params.seed is not None else 0)
    opening = rng.choice(OPENINGS).replace("Luna", params.name)
    dialogue = rng.choice(DIALOGUE).format(helper=params.helper)
    turn = rng.choice([
        "The sound was not decoration; it was a clue.",
        "The rhyme changed from a song into a map.",
        "When the last sound echoed, the real problem came clear.",
    ])

    world.say(opening)
    world.say(pattern.clue)
    world.para()
    world.say(f"{pattern.sound} The noises bounced through {setting.place}, and {params.name} tried to copy them.")
    world.say(f'"{pattern.rhyme.split(" / ")[0]} and {pattern.rhyme.split(" / ")[1]}," {params.name} rhymed, but guessed too fast.')
    world.say(dialogue)
    world.say(f"{params.name} listened again. {turn}")
    world.para()
    world.say(f"The exact rhyme was {pattern.rhyme}, and its sounds were {pattern.sound}")
    world.say(f"Following the pattern, {params.name} {pattern.action}.")
    world.say(f"{params.helper} cheered, and {params.name} answered, \"Now I know: a true rhyme can help us grow!\"")
    world.say(f"Together they smiled beneath the stars, because {pattern.lesson}.")
    world.say(f"At bedtime, the garden grew still, but one soft sound remained: {pattern.sound}")
    world.say("The rhyme was finished, and the good deed was exact.")

    hero.meters["care"] = 2
    hero.memes["confidence"] = 2
    hero.memes["listening"] = 2
    helper.memes["trust"] = 2
    world.facts = {
        "hero": hero,
        "helper": helper,
        "pattern": pattern,
        "sound": pattern.sound,
        "rhyme": pattern.rhyme,
        "action": pattern.action,
        "lesson": pattern.lesson,
        "place": setting.place,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        "Write a child-friendly rhyming story with exact rhymes and playful sound effects.",
        f"Tell a story in {facts['place']} where a sound becomes a helpful clue.",
        f"Use the rhyme {facts['rhyme']} and the sound effect {facts['sound']} in a story about careful listening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    return [
        QAItem(
            question=f"Where did {hero.id}'s adventure happen?",
            answer=f"{hero.id}'s adventure happened in {facts['place']}, where the sounds made a path.",
        ),
        QAItem(
            question=f"What exact rhyme did {hero.id} discover?",
            answer=f"{hero.id} discovered the exact rhyme {facts['rhyme']}. It helped turn the sound into a useful clue.",
        ),
        QAItem(
            question="What sound effects appeared in the story?",
            answer=f"The story used the sound effects {facts['sound']}. They helped the characters pay attention to the pattern.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} listened again and {facts['action']}. The careful second try made the rhyme useful.",
        ),
        QAItem(
            question=f"What did {hero.id} learn?",
            answer=f"{hero.id} learned that {facts['lesson']}.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{helper.id} helped {hero.id} slow down, listen, and follow the exact sound pattern.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern in which words have matching or similar ending sounds.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a written or performed sound that helps listeners imagine an action or place.",
        ),
        QAItem(
            question="What does exact mean?",
            answer="Exact means completely correct, precise, and matching without a change.",
        ),
        QAItem(
            question="Why can listening be helpful?",
            answer="Listening carefully can reveal clues, show what others need, and prevent hurried mistakes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("garden", "bell_path", "Luna", "rabbit", "Otis", "curious", 1),
    StoryParams("garden", "pond_echo", "Mira", "fox", "Wren", "gentle", 2),
    StoryParams("garden", "leaf_drum", "Pip", "mouse", "Tess", "brave", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        rows = asp_valid_combos()
        print(f"{len(rows)} valid combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(str(exc))
                return
            params.seed = seed
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
