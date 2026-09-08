#!/usr/bin/env python3
"""
A small animal storyworld about Eva, a helpful animal, and a secret in the air.

The domain models air, content, and Eva as physical and emotional entities.
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
    eva: str
    friend: str
    place: str
    content: str
    breeze: str
    problem: int = 0
    premise: int = 0
    dialogue: int = 0
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
    facts: dict[str, object] = field(default_factory=dict)
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


EVAS = ["Eva the fox", "Eva the rabbit", "Eva the squirrel", "Eva the otter"]
FRIENDS = ["Pip the mouse", "Mara the robin", "Toby the badger", "Nell the deer"]
PLACES = ["a green forest", "a sunny meadow", "a quiet riverbank", "an old orchard"]
CONTENTS = ["a bright blue feather", "a tiny bell", "a warm seed", "a red ribbon"]
BREEZES = ["a soft morning breeze", "a playful river wind", "a cool evening breeze", "a warm orchard wind"]

PROBLEMS = [
    {
        "lead": "{eva} carried {content} in a little leaf basket.",
        "trigger": "Then a gust of air lifted the basket's cover and sent {content} skittering toward the pond.",
        "risk": "If the air pushed it farther, the precious object might sink where nobody could reach it.",
        "action": "{eva} listened to the air and watched the grass bend. She placed three stones in a row to make a safe path, then asked {friend} to follow the moving {content}.",
        "resolution": "{friend} guided the basket with a twig while {eva} caught it beside a flat stone. The air grew gentle, and {content} rested safely inside.",
        "cause": "a gust of air carried the basket toward the pond",
        "deed": "watched the bending grass, made a stone path, and worked with the friend",
        "result": "the friend guided the basket back and Eva caught it beside a flat stone",
    },
    {
        "lead": "{eva} found {content} beneath a fern and tucked it carefully into her scarf.",
        "trigger": "A swirl of air tugged the scarf loose and pulled one end through a thorn bush.",
        "risk": "The more the scarf fluttered, the tighter the thorn held it.",
        "action": "{eva} stopped pulling. 'The air is showing us which way to turn,' she said, and she asked {friend} to hold the scarf still while she loosened the thorn.",
        "resolution": "Together they freed the scarf without tearing it. The content stayed bright, and the thorn bush waved harmlessly in the breeze.",
        "cause": "a swirl of air caught Eva's scarf on a thorn bush",
        "deed": "stopped pulling, read the wind, and asked the friend to hold the scarf still",
        "result": "they loosened the thorn and freed the scarf without damage",
    },
    {
        "lead": "{eva} and {friend} discovered {content} inside a hollow log.",
        "trigger": "Air whistled through the log and rolled the content toward its dark opening.",
        "risk": "One more puff might send it into a tunnel beneath the roots.",
        "action": "{eva} whispered, 'Quiet feet, gentle hands.' She and {friend} covered the far opening with a broad leaf before touching the content.",
        "resolution": "The next puff met the leaf and slowed. Eva reached in and brought the content into the sunlight.",
        "cause": "air rolled the content toward a tunnel beneath the roots",
        "deed": "covered the far opening with a leaf before reaching for the content",
        "result": "the leaf slowed the air and Eva brought the content into sunlight",
    },
    {
        "lead": "{eva} placed {content} on a stump so everyone could admire it.",
        "trigger": "A sudden pocket of air lifted it into a tall patch of grass.",
        "risk": "The grass hid the content, and every rustle sounded like it was moving farther away.",
        "action": "{eva} asked {friend} to stand still. She tossed a few dry leaves into the air and followed the leaves' path to find the hidden content.",
        "resolution": "The leaves circled one clump of grass. There lay {content}, safe beneath a daisy.",
        "cause": "a pocket of air lifted the content into tall grass",
        "deed": "used dry leaves to follow the moving air and locate the hidden content",
        "result": "the air led them to the content beneath a daisy",
    },
]

PREMISES = [
    "{eva} woke early in {place}. The air smelled of pine and wet leaves, and every bird seemed to be carrying a new song.",
    "In {place}, {eva} promised {friend} that they would protect one small treasure before sunset.",
    "{eva} was walking through {place} when the air brushed her whiskers. Something bright glittered beneath a fern.",
    "The animals of {place} gathered for a quiet morning walk. {eva} brought an empty leaf basket, just in case they found something special.",
]

DIALOGUES = [
    "'Can you feel the air changing?' asked {friend}. 'Yes,' said {eva}. 'It is telling us to slow down.'",
    "'What should we do?' asked {friend}. {eva} answered, 'We can listen first, then choose a careful step.'",
    "'I thought helping meant moving fast,' said {friend}. 'Sometimes helping means waiting,' replied {eva}.",
    "'Will the content be safe?' asked {friend}. 'It will be safer if we work together,' said {eva}.",
]

ENDINGS = [
    "At sunset, {eva} placed {content} in a dry nest beneath a wide leaf. The calm air curled around the shelter, as if the forest were breathing a thank-you.",
    "{friend} made a little sign that said, 'Protected by Eva and a Listening Friend.' The air fluttered the sign, but this time it could not carry it away.",
    "When the stars appeared, {eva} and {friend} shared berries beside the safe basket. They smiled whenever the air whispered through the trees.",
    "The next morning, {content} was still bright. {eva} taught the younger animals that the air was not an enemy; it was a clue.",
]

ASP_RULES = r"""
#show valid/4.
#show valid_story/5.

eva_name(E) :- eva(E).
friend_name(F) :- friend(F).
place_name(P) :- place(P).
content_name(C) :- content(C).
breeze_name(B) :- breeze(B).

valid(E, F, P, C) :-
    eva(E), friend(F), place(P), content(C).

valid_story(E, F, P, C, B) :-
    valid(E, F, P, C), breeze(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for value in EVAS:
        lines.append(asp.fact("eva", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend", value))
    for value in PLACES:
        lines.append(asp.fact("place", value))
    for value in CONTENTS:
        lines.append(asp.fact("content", value))
    for value in BREEZES:
        lines.append(asp.fact("breeze", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [
        (eva, friend, place, content, breeze)
        for eva in EVAS
        for friend in FRIENDS
        for place in PLACES
        for content in CONTENTS
        for breeze in BREEZES
    ]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: clingo gate matches valid_combos() ({len(expected)} combinations).")
        for params in build_curated():
            generate(params)
        print("OK: generated stories passed the Python story exercise.")
        return 0
    print("MISMATCH between Python and clingo combinations.")
    print("Only in Python:", sorted(expected - actual)[:5])
    print("Only in clingo:", sorted(actual - expected)[:5])
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal storyworld about Eva, air, and a treasured content.")
    parser.add_argument("--eva", choices=EVAS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--content", choices=CONTENTS)
    parser.add_argument("--breeze", choices=BREEZES)
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
        eva=args.eva or rng.choice(EVAS),
        friend=args.friend or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
        content=args.content or rng.choice(CONTENTS),
        breeze=args.breeze or rng.choice(BREEZES),
        problem=rng.randrange(len(PROBLEMS)),
        premise=rng.randrange(len(PREMISES)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    values = {
        "eva": params.eva,
        "friend": params.friend,
        "place": params.place,
        "content": params.content,
        "breeze": params.breeze,
    }
    problem = PROBLEMS[params.problem % len(PROBLEMS)]
    world = World()

    eva = world.add(Entity(
        id="eva",
        kind="animal",
        label=params.eva,
        memes={"curiosity": 1.0, "care": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="animal",
        label=params.friend,
        memes={"trust": 0.5, "worry": 0.0, "joy": 0.0},
    ))
    air = world.add(Entity(
        id="air",
        kind="nature",
        label=params.breeze,
        meters={"strength": 0.2, "motion": 0.0},
        memes={"mystery": 0.4},
    ))
    content = world.add(Entity(
        id="content",
        kind="object",
        label=params.content,
        meters={"safety": 1.0, "distance": 0.0},
        memes={"importance": 1.0},
    ))

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(f"{params.eva} noticed that the air moved around {params.content}, while {params.friend} watched from the edge of the path.")
    world.say(problem["lead"].format(**values))

    world.para()
    air.meters["strength"] = 1.0
    air.meters["motion"] = 1.0
    air.memes["mystery"] = 1.0
    content.meters["distance"] = 1.0
    content.meters["safety"] = 0.4
    eva.memes["care"] = 1.0
    friend.memes["worry"] = 1.0
    world.say(problem["trigger"].format(**values))
    world.say(problem["risk"].format(**values))
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(**values))
    world.say(problem["action"].format(**values))

    world.para()
    air.meters["strength"] = 0.1
    air.meters["motion"] = 0.0
    air.memes["mystery"] = 0.2
    content.meters["distance"] = 0.0
    content.meters["safety"] = 1.0
    eva.memes["relief"] = 1.0
    friend.memes["worry"] = 0.0
    friend.memes["joy"] = 1.0
    world.say(problem["resolution"].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        eva=params.eva,
        friend=params.friend,
        place=params.place,
        content=params.content,
        breeze=params.breeze,
        problem=params.problem % len(PROBLEMS),
        cause=problem["cause"],
        helpful_action=problem["deed"],
        result=problem["result"],
        danger=True,
        resolved=True,
        dialogue=True,
    )

    prompts = [
        "Write an animal story about Eva, air, and a treasured object that gets into trouble.",
        f"Tell a gentle animal story in which {params.eva} listens to the air and helps {params.friend}.",
        f"Write a child-friendly story about {params.content}, with dialogue and a careful solution.",
    ]

    story_qa = [
        QAItem(
            question="Who is the main animal in the story?",
            answer=f"The main animal is {params.eva}, who notices the air and takes care of {params.content}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble began because {problem['cause']}. This made {params.content} unsafe for a moment.",
        ),
        QAItem(
            question=f"How did {params.eva} help?",
            answer=f"{params.eva} {problem['deed']}. That careful choice helped protect the content.",
        ),
        QAItem(
            question="How did the animals solve the problem?",
            answer=f"They solved it when {problem['result']}. The air became calm and the content was safe.",
        ),
        QAItem(
            question="What did the dialogue change?",
            answer=f"The conversation helped {params.eva} and {params.friend} understand that they should slow down and work together.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is air?",
            answer="Air is the invisible mixture of gases around us. Moving air is called wind or a breeze.",
        ),
        QAItem(
            question="How can animals notice moving air?",
            answer="Animals can notice moving air through their fur, whiskers, feathers, skin, or the way leaves and grass bend.",
        ),
        QAItem(
            question="Why is dialogue useful in a story?",
            answer="Dialogue lets characters share clues, feelings, and plans, so their words can change what happens next.",
        ),
        QAItem(
            question="What does it mean to be careful?",
            answer="Being careful means noticing what could go wrong and choosing a safe action instead of rushing.",
        ),
        QAItem(
            question="Why do friends work together?",
            answer="Friends work together because different helpers can notice different clues and make a difficult task safer.",
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
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:8} ({entity.kind:7}) {' '.join(parts)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            eva="Eva the fox",
            friend="Pip the mouse",
            place="a green forest",
            content="a bright blue feather",
            breeze="a soft morning breeze",
            problem=0,
            premise=0,
            dialogue=0,
            ending=0,
        ),
        StoryParams(
            eva="Eva the rabbit",
            friend="Mara the robin",
            place="a sunny meadow",
            content="a tiny bell",
            breeze="a playful river wind",
            problem=1,
            premise=1,
            dialogue=1,
            ending=1,
        ),
        StoryParams(
            eva="Eva the squirrel",
            friend="Toby the badger",
            place="an old orchard",
            content="a warm seed",
            breeze="a warm orchard wind",
            problem=2,
            premise=2,
            dialogue=2,
            ending=2,
        ),
        StoryParams(
            eva="Eva the otter",
            friend="Nell the deer",
            place="a quiet riverbank",
            content="a red ribbon",
            breeze="a cool evening breeze",
            problem=3,
            premise=3,
            dialogue=3,
            ending=3,
        ),
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} valid animal-story combinations.")
        for eva, friend, place, content, breeze in combinations[:20]:
            print(f"  {eva}; {friend}; {place}; {content}; {breeze}")
        if len(combinations) > 20:
            print(f"  ... and {len(combinations) - 20} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            params.problem = seed % len(PROBLEMS)
            params.premise = (seed // len(PROBLEMS)) % len(PREMISES)
            params.dialogue = (seed // 3) % len(DIALOGUES)
            params.ending = (seed // 5) % len(ENDINGS)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.eva}: the air and {sample.params.content}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
