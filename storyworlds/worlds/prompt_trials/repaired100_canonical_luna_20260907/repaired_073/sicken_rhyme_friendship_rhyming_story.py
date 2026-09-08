#!/usr/bin/env python3
"""
A small rhyming storyworld about friendship, a sickened garden, and a careful fix.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = {
    "moonlit_garden": {
        "place": "the moonlit garden",
        "detail": "Silver moonlight rested on the leaves, while a little brook sang beside the beds.",
        "affords": {"gardening", "friendship"},
    },
    "rainy_rooftop": {
        "place": "the rainy rooftop garden",
        "detail": "Rain tapped the roof in a soft beat, and small pots stood in bright rows by the wall.",
        "affords": {"gardening", "friendship"},
    },
    "sunny_courtyard": {
        "place": "the sunny courtyard",
        "detail": "Warm bricks circled the garden, and bees hummed gently around the lavender.",
        "affords": {"gardening", "friendship"},
    },
}

NAMES = ["Luna", "Milo", "Pip", "Nora", "Cleo", "Tess", "Arlo", "Mina"]
FRIENDS = ["Mira", "Juno", "Bea", "Sol", "Finn", "Rae", "Theo", "Ivy"]
GENDERS = {
    "Luna": "girl", "Milo": "boy", "Pip": "child", "Nora": "girl",
    "Cleo": "girl", "Tess": "girl", "Arlo": "boy", "Mina": "girl",
    "Mira": "girl", "Juno": "girl", "Bea": "girl", "Sol": "child",
    "Finn": "boy", "Rae": "girl", "Theo": "boy", "Ivy": "girl",
}
TRAITS = ["kind", "curious", "cheerful", "patient", "brave", "thoughtful"]

INCIDENTS = [
    {
        "id": "wilting_mint",
        "arrival": "Luna found the mint looking faint and thin, with drooping leaves beneath the garden's grin.",
        "problem": "The mint had begun to sicken because a cracked pot let its water trickle away.",
        "mistake": "Luna poured and poured, but the thirsty soil still stayed dry by the door.",
        "clue": "Mira touched the pot and found a narrow crack beneath a mossy stack.",
        "plan": "They moved the mint to a sound clay pot, tucked soft soil around its roots, and shared one small cup of water.",
        "friend_line": "A flood is not friendship; a careful sip may help it grow.",
        "child_line": "Then we shall mend the pot and water the spot!",
        "result": "The mint stood up after the roots were sheltered and the leaking pot was set aside.",
        "ending": "By dawn, new mint leaves lifted green and bright, while the cracked pot held a small flower just right.",
        "lesson": "friendship means noticing what a friend truly needs instead of giving more of the wrong thing",
        "object": "mint",
    },
    {
        "id": "sickened_sunflower",
        "arrival": "A sunflower bent low in the garden row, and Luna whispered, “Why are you drooping so?”",
        "problem": "The flower had begun to sicken because a broad leaf blocked its morning light.",
        "mistake": "Luna tugged at the leaf too fast, and the sunflower shook with a worried blast.",
        "clue": "Mira noticed that the leaf belonged to a vine tied around the flower's stake.",
        "plan": "They loosened the vine gently, moved the stake a little, and let the sunflower face the day.",
        "friend_line": "A friend needs light and room, not a hurried tug that makes trouble bloom.",
        "child_line": "We will make a kinder space, at a slower pace.",
        "result": "The vine rested on a new trellis, and sunlight reached the sunflower without a fight.",
        "ending": "Its golden face turned toward the sun, and the two friends smiled when the careful work was done.",
        "lesson": "friendship grows when people pause, listen, and make room for one another",
        "object": "sunflower",
    },
    {
        "id": "coughing_basil",
        "arrival": "The basil leaves curled in a row, and Luna heard a tiny garden cough below.",
        "problem": "The basil had begun to sicken because its soil stayed soggy after too much rain.",
        "mistake": "Luna added more water, thinking a drink would make the wilted leaves cheer.",
        "clue": "Mira pressed the soil and found it wet and heavy near the roots.",
        "plan": "They moved the basil under a roof, loosened the soil, and waited for the roots to breathe.",
        "friend_line": "Not every cough needs a cup; sometimes dry air helps wake things up.",
        "child_line": "We will watch and wait, and help at the proper rate.",
        "result": "The basil dried safely, and its leaves began to uncurl in the gentle air.",
        "ending": "A fresh basil scent filled the breeze, and the little plant looked pleased.",
        "lesson": "a caring friend asks questions before choosing a cure",
        "object": "basil",
    },
    {
        "id": "pale_peas",
        "arrival": "The pea vines looked pale and slow, with tiny tendrils hanging in a row.",
        "problem": "The peas had begun to sicken because their climbing strings had fallen below the growing stems.",
        "mistake": "Luna pulled the vines upward, but one tender tendril gave a startled snap.",
        "clue": "Mira saw loose knots lying beneath the leaves beside the garden gate.",
        "plan": "They built a low frame, tied each vine with soft cloth, and checked that no stem was squeezed.",
        "friend_line": "A gentle tie can guide a climb; a tight one steals a plant's good time.",
        "child_line": "Softly we steer, so the peas can persevere.",
        "result": "The peas found the frame and began to climb without strain.",
        "ending": "Soon little flowers opened in a row, like stars where green vines grow.",
        "lesson": "friendship gives support without taking away another friend's space",
        "object": "pea vines",
    },
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None
    incident: int = 0
    rhyme: int = 0
    cadence: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming friendship story about a garden that begins to sicken."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "boy", "child"])
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--friend-gender", choices=["girl", "boy", "child"])
    parser.add_argument("--trait", choices=TRAITS)
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
    name = args.name or rng.choice(NAMES)
    friend_choices = [item for item in FRIENDS if item != name]
    friend = args.friend or rng.choice(friend_choices)
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        name=name,
        gender=args.gender or GENDERS[name],
        friend=friend,
        friend_gender=args.friend_gender or GENDERS[friend],
        trait=args.trait or rng.choice(TRAITS),
        incident=rng.randrange(len(INCIDENTS)),
        rhyme=rng.randrange(8),
        cadence=rng.randrange(64),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("The chosen place is not part of this garden storyworld.")
    if params.name == params.friend:
        raise StoryError("The child and friend must be different characters.")
    if params.gender not in {"girl", "boy", "child"}:
        raise StoryError("The main character must be a girl, boy, or child.")
    if params.friend_gender not in {"girl", "boy", "child"}:
        raise StoryError("The friend must be a girl, boy, or child.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = World(place=SETTINGS[params.place]["place"])

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0, "care": 0.7},
        memes={"friendship": 1.0, "hope": 0.8},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=params.friend_gender,
        label=params.friend,
        meters={"observation": 1.0, "patience": 0.9},
        memes={"friendship": 1.0, "trust": 0.8},
    ))
    plant = world.add(Entity(
        id="Plant",
        kind="living_thing",
        type=incident["object"].replace(" ", "_"),
        label=incident["object"],
        phrase=f"the {incident['object']}",
        meters={"health": 0.3, "water": 0.4, "shelter": 0.2},
        memes={"garden": 1.0},
    ))
    tool = world.add(Entity(
        id="CareTool",
        kind="thing",
        type="garden_tool",
        label="care tools",
        phrase="a little basket of garden tools",
        owner=child.id,
        meters={"useful": 1.0},
    ))

    rhyme_openings = [
        ("One moonlit night, with stars shining bright,", "Luna"),
        ("By rain-tapped pots in a silvery spot,", "Luna"),
        ("In a sunny square with warm golden air,", "Luna"),
        ("At twilight's gleam by a singing stream,", "Luna"),
    ]
    opening, _ = rhyme_openings[params.cadence % len(rhyme_openings)]
    opening = opening.replace("Luna", params.name)

    friendship_lines = [
        "A friendship is listening, steady and true; it starts with a question: “How are you?”",
        "A friend does not hurry, or boss, or decree; a friend looks closely and waits patiently.",
        "Two caring hearts, when they share what they know, can help a small garden begin to grow.",
        "A friend brings a hand, but also an ear; kind questions make muddled clues clear.",
    ]
    friendship_line = friendship_lines[(params.cadence // 4) % len(friendship_lines)]

    world.say(f"{opening}, {params.name}, a {params.trait} {params.gender}, went to {world.place} with {params.friend}, their good friend.")
    world.say(SETTINGS[params.place]["detail"])
    world.say(f"{friendship_line} They came to check the plants and sing a gentle rhyme.")
    world.say(incident["arrival"])
    world.para()

    world.say(incident["problem"])
    world.say(incident["mistake"])
    world.say(
        f'{params.name} said, "{incident["child_line"]}"'
    )
    world.say(
        f'{params.friend} replied, "{incident["friend_line"]}"'
    )
    world.say(
        f'"Let us look before we leap," said {params.friend}. '
        f'"A true friend helps with care, not merely with speed."'
    )
    world.say(
        f"{params.name} nodded. The two friends knelt beside the bed, keeping their hands gentle and their eyes wide."
    )
    world.para()

    world.say(f"Then {params.friend} noticed the clue: {incident['clue'][0].lower() + incident['clue'][1:]}")
    world.say(incident["plan"])
    world.say("They took turns, told the truth about what they saw, and made each careful step rhyme with the next.")
    world.say(f'"A little less guessing, a little more care," said {params.name}.')
    world.say(f'"A little more listening makes friendship grow fair," said {params.friend}.')
    world.say(incident["result"])
    world.para()

    world.say(f"{params.name} and {params.friend} watched the {incident['object']} breathe into a healthier day.")
    world.say(f"They learned that {incident['lesson']}.")
    world.say("The garden was not healed by a magic spell. It was helped by noticing, sharing, and choosing the right small action.")
    world.say(incident["ending"])
    world.say("And under the moon, rain, or sun, their friendship shone brighter than the work they had done.")

    plant.meters.update({"health": 1.0, "water": 0.8, "shelter": 1.0})
    plant.memes["hope"] = 1.0
    child.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    world.facts.update(
        child=child,
        friend=friend,
        plant=plant,
        tool=tool,
        incident=incident,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a rhyming story for a young child about {params.name} and {params.friend}, whose friendship helps a {incident['object']} that begins to sicken.",
        f"Tell a gentle friendship tale with dialogue, a garden problem, a careful turn, and a hopeful rhyming ending.",
        f"Write a child-facing rhyme in which friends discover that listening and evidence are better than a hurried guess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question="Who are the friends in the story?",
            answer=f"The friends are {params.name}, a {params.trait} {params.gender}, and {params.friend}, who work together in {world.place}.",
        ),
        QAItem(
            question=f"Why did the {incident['object']} begin to sicken?",
            answer=incident["problem"],
        ),
        QAItem(
            question="What mistake did the main character make at first?",
            answer=incident["mistake"],
        ),
        QAItem(
            question="What clue changed the friends' plan?",
            answer=incident["clue"],
        ),
        QAItem(
            question="How did the friends help the living thing?",
            answer=f"{incident['plan']} {incident['result']}",
        ),
        QAItem(
            question="What did the friends learn about friendship?",
            answer=f"They learned that {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when a plant begins to sicken?",
            answer="It means the plant is becoming unhealthy and may need a different kind of care.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern in which words have similar ending sounds, such as bright and night.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship in which people listen, help, trust, and enjoy time together.",
        ),
        QAItem(
            question="Why should someone look for clues before helping?",
            answer="Looking for clues helps a person choose the kind of help that is actually needed.",
        ),
        QAItem(
            question="Why can too much water hurt some plants?",
            answer="Too much water can leave soil soggy, making it hard for roots to breathe.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- rhyme, friendship, sickening_problem, careful_fix, dialogue.
"""


def asp_facts() -> str:
    return "\n".join([
        "rhyme.",
        "friendship.",
        "sickening_problem.",
        "careful_fix.",
        "dialogue.",
    ])


def asp_program(show: str = "#show compatible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        models = asp.solve(asp_program(), models=1)
        compatible = any(symbol.name == "compatible" for symbol in models[0]) if models else False
        if not compatible:
            print("ASP verification failed: no compatible story model.", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"ASP verification failed: {exc}", file=sys.stderr)
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or "friend" not in sample.story.lower():
            print("Python verification failed: missing friendship story.", file=sys.stderr)
            return 1
        if "sicken" not in sample.story.lower() and "sickened" not in sample.story.lower():
            print("Python verification failed: missing sicken premise.", file=sys.stderr)
            return 1
        if len(sample.story_qa) < 4:
            print("Python verification failed: insufficient story QA.", file=sys.stderr)
            return 1
    return 0


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
        lines.append(f"  {entity.id:10} ({entity.type:14}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moonlit_garden",
        name="Luna",
        gender="girl",
        friend="Mira",
        friend_gender="girl",
        trait="curious",
        incident=0,
        rhyme=1,
        cadence=3,
    ),
    StoryParams(
        place="rainy_rooftop",
        name="Milo",
        gender="boy",
        friend="Juno",
        friend_gender="girl",
        trait="patient",
        incident=2,
        rhyme=4,
        cadence=22,
    ),
    StoryParams(
        place="sunny_courtyard",
        name="Pip",
        gender="child",
        friend="Theo",
        friend_gender="boy",
        trait="cheerful",
        incident=3,
        rhyme=6,
        cadence=41,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        try:
            from storyworlds import asp
            model = asp.one_model(asp_program())
            print("compatible(story)." if any(symbol.name == "compatible" for symbol in model) else "No compatible story.")
        except Exception as exc:
            print(f"ASP unavailable: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: a rhyming friendship garden story"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
