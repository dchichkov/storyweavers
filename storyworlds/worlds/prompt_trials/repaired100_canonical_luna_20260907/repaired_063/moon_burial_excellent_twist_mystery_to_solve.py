#!/usr/bin/env python3
"""
A standalone storyworld: a heartwarming moonlit burial mystery with an excellent
twist.

A child finds a small burial mound beneath the moon. The mystery is not about
a secret treasure or a frightening ghost. Careful clues reveal that the mound
was made by a family of field mice to protect a fallen seed, and the excellent
twist is that the "burial" becomes the beginning of a living garden.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

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
    place: str = "the moonlit garden"


@dataclass
class StoryParams:
    name: str
    companion_name: str
    elder_name: str
    mystery_id: int = 0
    opening_mode: int = 0
    dialogue_mode: int = 0
    twist_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


MYSTERIES = [
    {
        "object": "a tiny mound of fresh earth beneath the moon",
        "question": "who had made the careful burial and what lay beneath it",
        "risk": "The earth was soft beside a steep flower bed, so the children stayed on the flat path and did not dig.",
        "wrong": "At first they wondered whether someone had buried a silver button or a little box.",
        "clues": "two rows of mouse prints, a husk-shaped hollow, and a trail of sunflower seeds leading from the shed",
        "cause": "A family of field mice had covered a fallen sunflower seed to keep it safe from hungry birds.",
        "action": "They marked the mound with three smooth stones, told the gardener, and watched from a respectful distance.",
        "result": "The gardener agreed to leave the patch undisturbed and placed a low twig fence around it.",
        "twist": "After a week of warm rain, a green shoot rose from the burial mound. The seed had not been hidden forever; it had been given a safe beginning.",
        "lesson": "A gentle mystery can hold a hopeful surprise.",
        "image": "Under the next full moon, the young sunflower opened one golden face beside the little twig fence.",
    },
    {
        "object": "a round burial of blue pebbles beside the moon gate",
        "question": "why the pebbles formed a circle and who had arranged them",
        "risk": "The gate stood near a pond, so everyone remained on the dry stepping stones and kept their hands away from the water.",
        "wrong": "The circle looked like a spell, and the children briefly imagined that moon fairies had left it.",
        "clues": "small webbed tracks, bits of pond reed, and matching blue pebbles along the shallow bank",
        "cause": "A duck had carried the pebbles in its bill while building a sheltered nest near the reeds.",
        "action": "They asked the pond keeper for help, and she moved the path sign rather than disturbing the nest.",
        "result": "Visitors could walk safely around the nesting place while the duck returned without alarm.",
        "twist": "The burial circle became a nest marker, and three ducklings later waddled through it as if it were a moon gate.",
        "lesson": "The kindest answer leaves room for living things.",
        "image": "Moonlight shone on three ducklings following their mother past the blue pebble circle.",
    },
    {
        "object": "a small burial mound beneath the old apple tree",
        "question": "whether someone had buried a lost keepsake there",
        "risk": "One branch had fallen nearby, so the children stayed clear of the tree and waited for the orchard keeper.",
        "wrong": "A ribbon caught in the grass made them think a child had hidden a birthday present.",
        "clues": "a chewed apple core, squirrel tracks, and a red ribbon tied safely to a low branch",
        "cause": "A squirrel had buried an apple seed while a gardener tied the ribbon to mark a branch that needed pruning.",
        "action": "They showed the clues to the orchard keeper, who removed the loose branch and left the seedbed alone.",
        "result": "The tree became safe, and the ribbon remained as a bright reminder to watch for new growth.",
        "twist": "Months later, a tiny apple tree appeared beside the old one, making the burial a promise of another orchard.",
        "lesson": "A careful look can turn a worry into a future.",
        "image": "The moon hung above two apple trees, one tall and one young, sharing the same silver light.",
    },
    {
        "object": "a folded cloth resting in a shallow burial near the lantern path",
        "question": "why the cloth had been covered with leaves",
        "risk": "The path bordered a sleeping garden, so the children used their lanterns from far away and did not pull at the cloth.",
        "wrong": "They guessed that a traveler had buried a secret map.",
        "clues": "a loose button, a trail from the laundry basket, and a faint warm scent of lavender",
        "cause": "A breeze had blown the gardener's cloth beneath leaves, where a hedgehog used it as a warm resting place.",
        "action": "They called the gardener, who waited until the hedgehog left before retrieving the cloth.",
        "result": "The cloth was washed, and a small shelter was placed nearby for the garden visitor.",
        "twist": "The burial had looked like a lost object, but it had quietly become a bed for a tired hedgehog.",
        "lesson": "Waiting can be an act of kindness.",
        "image": "The hedgehog curled beneath the new shelter while the moon silvered the clean cloth on the line.",
    },
]

NAMES = ["Luna", "Mara", "Theo", "Nia", "Iris", "Owen", "Sami", "Cleo"]
COMPANIONS = ["Pip", "Jun", "Milo", "Wren", "Tess", "Bo"]
ELDERS = ["Grandma Rose", "Aunt May", "Mr. Rowan", "Nana June"]

OPENINGS = [
    "One quiet evening,",
    "After a soft summer rain,",
    "When the first stars appeared,",
    "On the night the garden smelled of lavender,",
    "As the moon climbed over the fence,",
]

DIALOGUES = [
    '"Let us look before we guess," said {companion}. "The ground may be telling us something."',
    '"Should we uncover it?" asked {name}. "No," said {elder}. "Careful clues are better than a hurried hand."',
    '"I see tiny tracks," whispered {name}. "Then someone small may need this place to stay peaceful," said {elder}.',
    '"A mystery can be exciting without being scary," said {companion}. "We can solve it gently," agreed {name}.',
]

TWIST_LEADS = [
    "The answer brought an excellent twist.",
    "Then the mystery turned in an excellent new direction.",
    "Just when they thought the burial meant an ending, an excellent surprise appeared.",
    "The moonlit clues revealed a twist no one had expected.",
]

ENDINGS = [
    "Luna felt warm inside, because solving the mystery had helped them protect something small.",
    "They went home quietly, carrying no treasure except the happy knowledge that they had cared well.",
    "The garden seemed brighter, as though the moon itself approved of their patient kindness.",
    "Everyone agreed that the best mysteries do not merely reveal the past; sometimes they make room for tomorrow.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTING = Setting()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming moon burial mystery storyworld."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion-name")
    parser.add_argument("--elder-name")
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
    companion = args.companion_name or rng.choice(COMPANIONS)
    elder = args.elder_name or rng.choice(ELDERS)
    return StoryParams(
        name=name,
        companion_name=companion,
        elder_name=elder,
        mystery_id=rng.randrange(len(MYSTERIES)),
        opening_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        twist_mode=rng.randrange(len(TWIST_LEADS)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.companion_name.strip():
        raise StoryError("companion_name must not be empty")
    if not params.elder_name.strip():
        raise StoryError("elder_name must not be empty")
    if not 0 <= params.mystery_id < len(MYSTERIES):
        raise StoryError("mystery_id does not select a known mystery")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    mystery = MYSTERIES[params.mystery_id]
    world = World(SETTING)

    child = world.add(
        Entity(
            id="child",
            kind="character",
            type="child",
            label=params.name,
            memes={"curiosity": 1.0, "care": 0.0},
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type="friend",
            label=params.companion_name,
            memes={"patience": 1.0},
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type="garden_keeper",
            label=params.elder_name,
            memes={"wisdom": 1.0},
        )
    )
    moon = world.add(
        Entity(
            id="moon",
            kind="celestial",
            type="moon",
            label="the moon",
            meters={"light": 1.0},
            memes={"calm": 1.0},
        )
    )
    burial = world.add(
        Entity(
            id="burial",
            kind="place",
            type="burial",
            label=mystery["object"],
            meters={"disturbed": 0.0, "protected": 0.0},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="evidence",
            type="clue_set",
            label=mystery["clues"],
            meters={"observed": 0.0},
        )
    )

    world.facts.update(
        child=child,
        companion=companion,
        elder=elder,
        moon=moon,
        burial=burial,
        clue=clue,
        mystery=mystery,
        params=params,
        solved=False,
        twist_revealed=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]
    child: Entity = facts["child"]
    companion: Entity = facts["companion"]
    elder: Entity = facts["elder"]
    moon: Entity = facts["moon"]
    burial: Entity = facts["burial"]
    mystery: dict[str, str] = facts["mystery"]

    opening = OPENINGS[params.opening_mode % len(OPENINGS)]
    dialogue = DIALOGUES[params.dialogue_mode % len(DIALOGUES)].format(
        name=child.label,
        companion=companion.label,
        elder=elder.label,
    )
    twist_lead = TWIST_LEADS[params.twist_mode % len(TWIST_LEADS)]
    ending = ENDINGS[params.ending_mode % len(ENDINGS)]

    world.say(
        f"{opening} {child.label} walked with {companion.label} through {world.setting.place}."
    )
    world.say(
        f"{moon.label} shone over {burial.label}, and the sight made the two friends stop."
    )
    world.say(
        f"They had a mystery to solve: {mystery['question']}."
    )

    world.para()
    world.say(mystery["risk"])
    world.say(mystery["wrong"])
    world.say(dialogue)
    world.say(
        f"{elder.label} came along the path and said, "
        f'"A mystery deserves patience. We can learn without harming what we find."'
    )

    world.para()
    world.say(
        f"From the safe path, they noticed {mystery['clues']}."
    )
    world.say(
        f"{child.label} pointed to the pattern while {companion.label} held the lantern steady."
    )
    world.say(mystery["cause"])
    world.say(
        f"{elder.label} nodded. The clues matched, so the children decided not to disturb the burial."
    )

    world.para()
    world.say(mystery["action"])
    world.say(mystery["result"])
    world.say(twist_lead)
    world.say(mystery["twist"])

    world.para()
    world.say(ending)
    world.say(mystery["lesson"])
    world.say(mystery["image"])

    burial.meters["protected"] = 1.0
    clue.meters["observed"] = 1.0
    child.memes["care"] = 1.0
    facts["solved"] = True
    facts["twist_revealed"] = True


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    return [
        'Write a heartwarming child-facing story that includes the words "moon", "burial", and "excellent".',
        f"Tell a gentle mystery to solve about {mystery['object']} without unsafe digging.",
        "Include a brief dialogue exchange, careful clues, a hopeful twist, and an ending image showing what changed.",
    ]


def story_questions(world: World) -> list[QAItem]:
    facts = world.facts
    child: Entity = facts["child"]
    companion: Entity = facts["companion"]
    elder: Entity = facts["elder"]
    mystery: dict[str, str] = facts["mystery"]
    return [
        QAItem(
            question=f"What did {child.label} and {companion.label} find?",
            answer=f"They found {mystery['object']}.",
        ),
        QAItem(
            question="What mystery did they want to solve?",
            answer=f"They wanted to know {mystery['question']}.",
        ),
        QAItem(
            question="What clues helped them understand the burial?",
            answer=f"The clues were {mystery['clues']}.",
        ),
        QAItem(
            question="What caused the burial?",
            answer=mystery["cause"],
        ),
        QAItem(
            question=f"How did {elder.label} help?",
            answer="The elder encouraged everyone to use patience, observe from a safe path, and avoid disturbing the burial.",
        ),
        QAItem(
            question="What was the excellent twist?",
            answer=mystery["twist"],
        ),
    ]


def world_knowledge_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burial?",
            answer="A burial is the careful placing and covering of something in the ground, often to honor a person or protect a seed or object.",
        ),
        QAItem(
            question="Why should people avoid digging into an unknown mound?",
            answer="They should avoid digging because the mound may protect an animal, a plant, or a dangerous object, and an adult can help investigate safely.",
        ),
        QAItem(
            question="Why are clues useful in a mystery?",
            answer="Clues are useful because they provide evidence that helps people replace guesses with a careful explanation.",
        ),
        QAItem(
            question="What makes a twist hopeful?",
            answer="A hopeful twist changes what seemed sad or worrying into a safe discovery, a new beginning, or a chance to care for someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.type:12}) {' '.join(state)}"
        )
    lines.append(
        f"  solved={world.facts['solved']} twist_revealed={world.facts['twist_revealed']}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
observed_clues :- clue_set(observed).
safe_choice :- burial(protected).
gentle_mystery :- moon(shines), observed_clues, safe_choice.
hopeful_twist :- seed(growing).
good_story :- gentle_mystery, hopeful_twist.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("moon", "shines"),
            asp.fact("clue_set", "observed"),
            asp.fact("burial", "protected"),
            asp.fact("seed", "growing"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    good = any(symbol.name == "good_story" for symbol in model)
    if not good:
        print("MISMATCH: ASP twin rejected the gentle moon burial story.")
        return 1

    params = StoryParams(
        name="Luna",
        companion_name="Pip",
        elder_name="Grandma Rose",
        mystery_id=0,
        seed=1,
    )
    sample = generate(params)
    required = ("moon", "burial", "excellent")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated prose is missing a required seed word.")
        return 1
    if not sample.story_qa or not sample.world_qa:
        print("MISMATCH: generated story is missing QA.")
        return 1

    print("OK: Python and ASP agree on a safe, clue-based, hopeful mystery.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_knowledge_questions(world),
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


CURATED = [
    StoryParams(
        name="Luna",
        companion_name="Pip",
        elder_name="Grandma Rose",
        mystery_id=0,
        seed=101,
    ),
    StoryParams(
        name="Iris",
        companion_name="Wren",
        elder_name="Nana June",
        mystery_id=1,
        seed=102,
    ),
    StoryParams(
        name="Mara",
        companion_name="Milo",
        elder_name="Mr. Rowan",
        mystery_id=2,
        seed=103,
    ),
    StoryParams(
        name="Theo",
        companion_name="Jun",
        elder_name="Aunt May",
        mystery_id=3,
        seed=104,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("good_story" if any(symbol.name == "good_story" for symbol in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        seen: set[str] = set()
        attempts = max(args.n * 20, 20)
        for offset in range(attempts):
            if len(samples) >= args.n:
                break
            current_seed = base_seed + offset
            rng = random.Random(current_seed)
            params = resolve_params(args, rng)
            params.seed = current_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("no stories were generated")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and the moonlit burial"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
