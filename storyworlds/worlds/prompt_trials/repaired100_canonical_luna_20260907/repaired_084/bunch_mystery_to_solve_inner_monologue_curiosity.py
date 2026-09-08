#!/usr/bin/env python3
"""
A small mythic storyworld about a mysterious bunch of golden berries.
Luna must follow her curiosity, listen to her inner thoughts, and solve
the mystery before the moon festival begins.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    companion_name: str
    season: str
    scenario_id: int = 0
    thought_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Luna", "Mira", "Tala", "Nia", "Suri", "Rin"]
COMPANIONS = ["Pax", "Oro", "Milo", "Kiko", "Bram", "Ivo"]
SEASONS = ["spring", "summer", "autumn", "winter"]

SCENARIOS = [
    {
        "place": "the hill beneath the moon tree",
        "bunch": "a bunch of silver berries",
        "mystery": "why the berries glowed only when no one touched them",
        "clue": "small blue footprints circled the roots, but none led away",
        "test": "Luna placed a fallen leaf beside the bunch and watched its shadow",
        "answer": "the berries were moon seeds waiting for a quiet song",
        "resolution": "she sang softly instead of grabbing them",
        "image": "The berries rose like tiny stars and settled into the moon tree's branches.",
    },
    {
        "place": "the stone bridge over the cloud stream",
        "bunch": "a bunch of red feathers",
        "mystery": "who had tied the feathers into a knot shaped like a crown",
        "clue": "each feather carried a speck of gold dust from the mountain shrine",
        "test": "Luna followed the dust with a polished acorn",
        "answer": "the wind spirit had made the crown to ask for help",
        "resolution": "she untied the crown carefully and read the pattern in its feathers",
        "image": "The loosened feathers flew upward and formed a bright path to the shrine.",
    },
    {
        "place": "the quiet garden of sleeping statues",
        "bunch": "a bunch of little bells",
        "mystery": "why the bells rang whenever someone told a lie",
        "clue": "the bells stayed still when Luna admitted that she was afraid",
        "test": "Luna asked the statues questions and answered them honestly",
        "answer": "the bells were guarding a promise made by the first gardener",
        "resolution": "she spoke the truth about the missing watering cup",
        "image": "The statues opened their stone hands, revealing the cup beneath a rose.",
    },
    {
        "place": "the cave behind the waterfall",
        "bunch": "a bunch of warm blue stones",
        "mystery": "why the stones were warm though the cave was full of ice",
        "clue": "their warmth grew stronger near a crack shaped like a sleeping eye",
        "test": "Luna held a thread near the crack and saw it drift inward",
        "answer": "a hidden dragon was breathing behind the wall",
        "resolution": "she tapped a gentle rhythm to show she came as a friend",
        "image": "The dragon opened one kind eye, and the blue stones lit the cave like dawn.",
    },
    {
        "place": "the village roof where the clouds came to rest",
        "bunch": "a bunch of golden ribbons",
        "mystery": "why the ribbons pointed toward different homes",
        "clue": "every ribbon ended at a door where someone needed help",
        "test": "Luna counted the ribbons and matched them to the village bells",
        "answer": "the sky guardian had woven a map of kindness",
        "resolution": "she carried the ribbons to the neighbors and asked what they needed",
        "image": "By sunset, every golden ribbon was tied to a grateful door.",
    },
]

THOUGHTS = [
    "Luna thought, 'A strange thing is not a frightening thing yet. It is a question waiting for careful feet.'",
    "Luna wondered, 'What if the mystery is asking me to listen rather than hurry?'",
    "Inside her mind, Luna said, 'I can be curious and cautious at the same time.'",
    "Luna thought, 'The smallest clue may be holding the largest answer.'",
    "Her inner voice whispered, 'Do not break what you do not understand.'",
    "Luna told herself, 'A mystery grows clearer when I make room for many possibilities.'",
]

DIALOGUES = [
    ('"Should we take the bunch home?"', '"Not until we know what it is asking us to do."'),
    ('"Perhaps the mystery is only a trick of the light,"', '"Then we can test the light without harming the bunch."'),
    ('"I am curious, but I am also nervous,"', '"Good," said her companion. "Nervous feet can still walk wisely."'),
    ('"What did you notice?"', '"That every clue points to a promise, not a prize."'),
    ('"May we touch it?"', '"Let us first ask whether it wants to be touched."'),
    ('"The answer feels close,"', '"Then let us be quiet enough to hear it."'),
]

ENDINGS = [
    "From that day on, Luna remembered that curiosity was a lantern, not a torch.",
    "The village learned that a mystery should be met with patience before certainty.",
    "Luna kept the lesson in her heart: wonder is strongest when it also protects.",
    "The old myth gained a new verse about the child who listened before she acted.",
    "Whenever the moon rose, Luna looked for another question hidden in the world.",
    "The companion smiled, knowing that courage had begun with a careful question.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic mystery story about a mysterious bunch.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--season", choices=SEASONS)
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
    companion = args.companion or rng.choice(COMPANIONS)
    season = args.season or rng.choice(SEASONS)
    if name == companion:
        companion = rng.choice([item for item in COMPANIONS if item != name])
    return StoryParams(
        name=name,
        companion_name=companion,
        season=season,
        scenario_id=rng.randrange(len(SCENARIOS)),
        thought_id=rng.randrange(len(THOUGHTS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.name or not params.companion_name:
        raise StoryError("Both the seeker and companion need names.")
    if params.name == params.companion_name:
        raise StoryError("The seeker and companion must be different characters.")
    if params.season not in SEASONS:
        raise StoryError(f"Unknown season: {params.season}.")
    if not 0 <= params.scenario_id < len(SCENARIOS):
        raise StoryError("Scenario choice is outside the story registry.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    scenario = SCENARIOS[params.scenario_id]
    dialogue = DIALOGUES[params.dialogue_id % len(DIALOGUES)]

    world = World()
    seeker = world.add(Entity("seeker", "character", "child", params.name))
    companion = world.add(Entity("companion", "character", "friend", params.companion_name))
    bunch = world.add(Entity("bunch", "object", "mystery", scenario["bunch"]))
    moon = world.add(Entity("moon_tree", "place", "sacred_place", scenario["place"]))

    world.facts.update(
        scenario=scenario,
        seeker=seeker,
        companion=companion,
        bunch=bunch,
        moon=moon,
        resolved=False,
        curiosity=True,
        safe_method=False,
        clue_found=False,
    )

    seeker.memes["curiosity"] = 1.0
    seeker.memes["caution"] = 1.0
    bunch.meters["mystery"] = 1.0

    world.say(
        f"In the {params.season}, when the moon walked low over the world, "
        f"{params.name} and {params.companion_name} found {scenario['bunch']} at {scenario['place']}."
    )
    world.say(
        f"It was not an ordinary bunch. The mystery was {scenario['mystery']}, "
        "and even the air seemed to hold its breath."
    )

    world.para()
    world.say(THOUGHTS[params.thought_id % len(THOUGHTS)])
    world.say(f"{params.name} asked, {dialogue[0]} {params.companion_name} answered, {dialogue[1]}")
    world.say(
        f"Instead of pulling at the bunch, {params.name} looked closely and found that "
        f"{scenario['clue']}."
    )
    world.facts["clue_found"] = True
    seeker.memes["curiosity"] += 1.0
    seeker.memes["patience"] = 1.0

    world.para()
    world.say(
        f"First, {scenario['test']}. The test revealed a pattern, but the pattern was too small "
        "to understand by force."
    )
    world.say(
        f"{params.name} asked, {dialogue[2]} {params.companion_name} replied, {dialogue[3]}"
    )
    world.say(
        f"Then {params.name} remembered the oldest rule of the moon people: "
        "when a wonder is alive, kindness must come before ownership."
    )
    world.say(f"So {scenario['resolution']}.")
    world.facts["safe_method"] = True
    world.facts["answer"] = scenario["answer"]
    bunch.meters["mystery"] = 0.0
    bunch.meters["understood"] = 1.0
    seeker.memes["wisdom"] = 1.0

    world.para()
    world.say(f"The answer was that {scenario['answer']}.")
    world.say(scenario["image"])
    world.say(ENDINGS[params.ending_id % len(ENDINGS)])
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    scenario = world.facts["scenario"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a myth about {params.name} solving a mystery involving {scenario['bunch']}.",
            f"Include an inner monologue showing why {params.name} stays curious but careful at {scenario['place']}.",
            f"Show {params.name} and {params.companion_name} using dialogue to discover that {scenario['answer']}.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    seeker = world.facts["seeker"]
    companion = world.facts["companion"]
    return [
        QAItem(
            "What did the children find?",
            f"{seeker.label} and {companion.label} found {scenario['bunch']} at {scenario['place']}.",
        ),
        QAItem(
            "What mystery did they need to solve?",
            f"They needed to discover {scenario['mystery']}.",
        ),
        QAItem(
            "What clue helped them?",
            f"They noticed that {scenario['clue']}.",
        ),
        QAItem(
            "How did they investigate safely?",
            f"They tested the mystery gently: {scenario['test']}.",
        ),
        QAItem(
            "What was the answer?",
            f"The answer was that {scenario['answer']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a bunch?",
            "A bunch is a group of things gathered or held together.",
        ),
        QAItem(
            "What is curiosity?",
            "Curiosity is the wish to learn or find out more about something.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is the stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            "What is a myth?",
            "A myth is an old-style story that uses marvelous events to explore important ideas.",
        ),
        QAItem(
            "Why should someone be careful with a mystery?",
            "Careful investigation helps a person learn the truth without damaging what they do not yet understand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.id}: {entity.label} meters={meters} memes={memes}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_domain(myth, bunch).
feature(mystery_to_solve).
feature(inner_monologue).
feature(curiosity).
clue_found :- feature(mystery_to_solve), feature(curiosity).
safe_investigation :- clue_found, feature(inner_monologue).
resolved_story :- safe_investigation.
#show resolved_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("domain", "myth"),
            asp.fact("seed_word", "bunch"),
            asp.fact("feature", "mystery_to_solve"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "curiosity"),
        ]
    )


def asp_program(show: str = "#show resolved_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    if not models:
        print("MISMATCH: ASP produced no model.")
        return 1
    atoms = set(asp.atoms(models[0], "resolved_story"))
    if atoms != {()}:
        print("MISMATCH: ASP story gate failed.")
        return 1

    params = StoryParams("Luna", "Pax", "spring", 0, 0, 0, 0, 17)
    sample = generate(params)
    required = ["bunch", "mystery", "curious", "thought", "answer"]
    text = sample.story.lower()
    if not all(word in text for word in required):
        print("MISMATCH: generated story lacks required narrative instruments.")
        return 1
    if not sample.world or not sample.world.facts.get("resolved"):
        print("MISMATCH: Python world did not resolve.")
        return 1
    print("OK: ASP/Python parity and generated story checks passed.")
    return 0


CURATED = [
    StoryParams("Luna", "Pax", "spring", 0, 0, 0, 0),
    StoryParams("Mira", "Oro", "summer", 1, 1, 2, 1),
    StoryParams("Tala", "Kiko", "autumn", 2, 3, 4, 2),
]


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
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
