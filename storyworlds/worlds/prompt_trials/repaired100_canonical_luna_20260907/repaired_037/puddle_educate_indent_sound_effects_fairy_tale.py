#!/usr/bin/env python3
"""
A fairy-tale storyworld about a puddle, a lesson, and a mysterious indentation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    fairy_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    lesson: int = 0
    ending: int = 0


SETTINGS = {
    "meadow": Setting("the moonlit meadow", {"puddle", "path"}),
    "forest": Setting("the silver forest clearing", {"puddle", "path"}),
    "castle": Setting("the castle garden", {"puddle", "path"}),
}

HERO_NAMES = ["Lina", "Milo", "Nora", "Theo", "Iris", "Pip"]
FAIRY_NAMES = ["Faye", "Luma", "Tilla", "Wren", "Sola", "Miri"]

INCIDENTS = [
    {
        "puddle": "a round puddle shining like a fallen star",
        "indent": "a deep indentation shaped like a tiny crown",
        "guess": "a moon giant had stepped there",
        "sound": "Plip-plop! Plip-plop!",
        "clue": "small silver feathers rested beside the wet mark",
        "truth": "a swan had landed after the rain and pressed one webbed foot into the soft earth",
        "repair": "The fairy guided the swan to a dry reed bank and taught the villagers to leave a gentle landing place.",
        "lesson": "a strange mark should be studied with clues instead of guessed at in fear",
        "ending": "By dawn, the puddle held the pink sky, and the little indentation was only a friendly memory.",
    },
    {
        "puddle": "a blue puddle glowing beneath the elder tree",
        "indent": "a narrow indentation running through its muddy edge",
        "guess": "a river dragon had dragged its tail across the ground",
        "sound": "Ssswish! Drip-drop!",
        "clue": "a broken watering jar lay uphill, with a trail of damp moss behind it",
        "truth": "the gardener's jar had tipped and rolled through the rain",
        "repair": "The fairy mended the jar with a golden thread and showed everyone how water follows a slope.",
        "lesson": "learning how things move can make a mystery feel less frightening",
        "ending": "The repaired jar rested by the tree while the puddle winked quietly at the stars.",
    },
    {
        "puddle": "a puddle sparkling beside the village path",
        "indent": "a neat indentation like a row of little bells",
        "guess": "invisible goblins had marched through the water",
        "sound": "Ting-ting! Squish-squish!",
        "clue": "three bellflowers bent over the mud, and their round seedpods touched the ground",
        "truth": "the wind had rocked the bellflowers into the soft soil",
        "repair": "The fairy tied the flowers to slender sticks and taught the children how wind can leave patterns.",
        "lesson": "a careful observer can find an ordinary cause hiding inside a magical-looking clue",
        "ending": "The bellflowers chimed in the breeze, and no invisible goblins were needed for the music.",
    },
    {
        "puddle": "a puddle dark as blackberry jam under the bridge",
        "indent": "a long indentation curving toward the water",
        "guess": "a sleeping serpent had curled there",
        "sound": "Gloop! Gloop! Rumble!",
        "clue": "round stones were scattered beside the mark, and each was wet on one side",
        "truth": "the stream had spilled over and rolled the stones into the mud",
        "repair": "The fairy placed stepping stones above the damp bank and explained how rushing water reshapes earth.",
        "lesson": "safe distance and patient noticing help us understand powerful water",
        "ending": "The stream sang beneath the bridge, while the new stones made a dry road home.",
    },
]

OPENINGS = [
    "At twilight, {hero} walked through {place} with {fairy}, who carried a lantern made from a firefly's glow.",
    "Once upon a gentle evening, {hero} followed {fairy} along {place} to gather moon-daisies.",
    "The moon rose over {place} when {hero} and {fairy} heard a curious sound near the path.",
    "In a kingdom where puddles remembered the rain, {hero} met {fairy} beside {place}.",
]

LESSONS = [
    '"Let us educate our eyes before we alarm our hearts," said {fairy}.',
    '"We can educate ourselves with every clue," {fairy} replied. "Magic loves careful questions."',
    '"A true adventurer studies first," said {fairy}. "That is how we educate courage into wisdom."',
    '"I will help educate you about the marks of rain, wind, and animals," promised {fairy}.',
]

ENDINGS = [
    '"Now I know that a mark is a question, not an answer," said {hero}.',
    '"I learned to listen before I leap," {hero} told {fairy}.',
    '"The mystery became smaller when we learned more," said {hero}.',
    '"Next time, I will search for clues before I make a royal guess," promised {hero}.',
]


ASP_RULES = r"""
#show valid/2.
setting(meadow). setting(forest). setting(castle).
affords(meadow,puddle). affords(meadow,path).
affords(forest,puddle). affords(forest,path).
affords(castle,puddle). affords(castle,path).
valid(P,F) :- setting(P), affords(P,F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for feature in sorted(setting.affords):
            lines.append(asp.fact("affords", name, feature))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, feature) for place, setting in SETTINGS.items() for feature in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(setting)

    hero = world.add(Entity(
        params.hero_name, "character", "child",
        meters={"distance_to_puddle": 3.0},
        memes={"curiosity": 1.0, "confidence": 0.4},
    ))
    fairy = world.add(Entity(
        params.fairy_name, "character", "fairy",
        meters={"distance_to_puddle": 3.0},
        memes={"wisdom": 1.0, "patience": 1.0},
    ))
    puddle = world.add(Entity(
        "puddle", "thing", "water", label="the puddle",
        meters={"depth": 0.08, "width": 1.2},
        memes={"mystery": 0.8},
    ))
    footprint = world.add(Entity(
        "indentation", "thing", "mark", label="the indentation",
        meters={"depth": 0.04},
        memes={"evidence": 1.0},
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        hero=hero.id, fairy=fairy.id, place=setting.place
    ))
    world.say(f"There they found {incident['puddle']} and {incident['indent']}.")
    world.say(
        f'"Perhaps {incident["guess"]}," whispered {hero.id}. '
        f'"Perhaps," said {fairy.id}, "but a fairy tale still needs evidence."'
    )

    world.para()
    world.say(f"Then the puddle trembled. {incident['sound']}")
    world.say(f'{hero.id} took one step toward it, but {fairy.id} lifted a bright hand.')
    world.say(LESSONS[params.lesson % len(LESSONS)].format(fairy=fairy.id))
    world.say(
        f'"Tell me what you notice," said {fairy.id}. '
        f'"I see {incident["clue"]}," answered {hero.id}.'
    )
    world.say(
        f"They stayed on the firm path and watched. The clue showed that {incident['truth']}."
    )
    hero.memes["confidence"] = 1.0
    hero.memes["curiosity"] = 0.7
    world.facts["resolved"] = True

    world.para()
    world.say(
        f'{fairy.id} smiled. "You helped solve it, {hero.id}. Learning is a kind of magic."'
    )
    world.say(incident["repair"])
    world.say(f'{ENDINGS[params.ending % len(ENDINGS)].format(hero=hero.id)}')
    world.say(incident["ending"])

    world.facts.update(
        hero=hero,
        fairy=fairy,
        puddle=puddle,
        indentation=footprint,
        incident=incident,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    incident = world.facts["incident"]
    return [
        f"Write a fairy tale about {incident['puddle']} and {incident['indent']}.",
        "Tell a child-friendly story where a fairy helps someone educate themselves through careful clues.",
        "Use vivid sound effects, dialogue, a harmless mystery, and a peaceful magical ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    hero = f["hero"].id
    fairy = f["fairy"].id
    return [
        QAItem(
            "Who found the mysterious puddle?",
            f"{hero} found the puddle while walking with {fairy} through {world.setting.place}.",
        ),
        QAItem(
            "What did the indentation first seem to be?",
            f"It seemed to be evidence that {incident['guess']}, but the characters waited for better clues.",
        ),
        QAItem(
            "What clue helped explain the mark?",
            f"They noticed that {incident['clue']}. This helped show that {incident['truth']}.",
        ),
        QAItem(
            "How did the fairy educate the traveler?",
            f"{fairy} taught {hero} to observe safely, ask questions, and use several clues before deciding what happened.",
        ),
        QAItem(
            "What changed by the end?",
            f"{hero} became more confident and learned that {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a puddle?",
            "A puddle is a small pool of water that gathers on the ground, often after rain.",
        ),
        QAItem(
            "What is an indentation?",
            "An indentation is a hollow or pressed-in place on a surface.",
        ),
        QAItem(
            "Why is it useful to study clues before guessing?",
            "Studying clues helps people find a safer and more accurate explanation instead of trusting a frightening first guess.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    fairy_name = args.fairy or rng.choice(FAIRY_NAMES)
    if hero_name == fairy_name:
        fairy_name = rng.choice([name for name in FAIRY_NAMES if name != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        fairy_name=fairy_name,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        lesson=rng.randrange(len(LESSONS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale storyworld about a puddle and an indentation."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--fairy")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:")
        for place, feature in asp_valid():
            print(f"  {place:10} {feature}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                hero_name=f"{place.title()}Traveler",
                fairy_name=f"{place.title()}Fairy",
                incident=index % len(INCIDENTS),
                opening=index % len(OPENINGS),
                lesson=index % len(LESSONS),
                ending=index % len(ENDINGS),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
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
