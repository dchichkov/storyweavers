#!/usr/bin/env python3
"""
Standalone storyworld: inventor / rhyme / foreshadowing / tall tale.

A playful inventor builds a rhyming machine whose early clues predict a
wobbling finale. The machine's problem is solved by listening to the rhyme,
not by making the biggest guess.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Workshop:
    place: str = "the hilltop workshop"
    roof: str = "a copper roof"
    floor: str = "a springy wooden floor"


@dataclass
class World:
    workshop: Workshop
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
    inventor_name: str
    helper_name: str
    invention_name: str = "The Rhyme Flyer"
    scenario: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


INVENTOR_NAMES = ["Luna", "Milo", "Tessa", "Orin", "Pia", "Bram", "Nia", "Felix"]
HELPER_NAMES = ["Jun", "Mara", "Otto", "Bea", "Cleo", "Finn", "Ivy", "Sol"]
GIRL_NAMES = {"Luna", "Tessa", "Pia", "Nia", "Mara", "Bea", "Cleo", "Ivy"}

OPENINGS = [
    "On the tallest hill in the county, the sunrise arrived wearing a hat made of pink thunder.",
    "One Tuesday morning, the village chickens crowed backward because the workshop chimney was humming.",
    "At noon, the clouds gathered like an audience, for everyone knew the inventor was testing something enormous.",
    "Long ago, when spoons were still considered adventurous tools, a bright workshop stood above the valley.",
    "On a windy day, the hilltop workshop shook so hard that three teacups marched in a circle.",
    "Before breakfast, the village bell rang twice, sneezed once, and pointed toward the inventor's door.",
    "At the edge of a valley wide enough to lose a sandwich in, an inventor prepared a machine taller than a barn.",
    "The day began quietly, which was suspicious, because every good invention nearby had a habit of making an entrance.",
]

SCENARIOS = [
    {
        "purpose": "carry a cheerful rhyme across the valley to wake the sleepy town",
        "materials": "copper pipes, kite cloth, seven brass bells, and one very determined wheel",
        "foreshadow": "the left wheel squeaked whenever the machine rolled toward the wind",
        "rhyme": "When the left wheel sings, tie down the wings",
        "problem": "the machine rose too early, spun above the rooftops, and began scattering rhyme cards like confetti",
        "turn": "remembered the squeak, tied the kite cloth, and moved the heavy bell from the top to the low axle",
        "result": "the machine floated steadily and sang its message into every lane",
        "image": "the copper flyer drifted over the valley, ringing a rhyme while children gathered below",
        "lesson": "A small warning can point toward a large solution when someone is willing to listen.",
    },
    {
        "purpose": "deliver a rhyming weather warning before a giant rainstorm arrived",
        "materials": "tin wings, a cloud-shaped drum, silver string, and a kettle with a speaking spout",
        "foreshadow": "the speaking spout puffed three tiny clouds whenever the damp wind blew",
        "rhyme": "When three clouds puff, close the stuff",
        "problem": "the machine opened every umbrella in the village at once and sent them bouncing toward the river",
        "turn": "counted the three puffs, closed the loose umbrella rack, and turned the drum toward the darkening sky",
        "result": "the weather warning boomed clearly before the first fat raindrop fell",
        "image": "umbrellas stood safely in their hooks while the machine beat a brave rhythm beneath the rain",
        "lesson": "Foreshadowing is useful because an early little clue may tell you how to prevent later trouble.",
    },
    {
        "purpose": "lead a parade of friendly robots through the village square",
        "materials": "wooden knees, red ribbons, a music box, and a pocket-sized compass",
        "foreshadow": "the compass needle pointed at the bakery whenever the robots needed to turn",
        "rhyme": "When the needle smells bread, turn instead",
        "problem": "the robots marched straight toward the bakery and formed a brass line around the baker's pies",
        "turn": "noticed the bread-loving needle, swapped it for the tested compass, and taught the robots the turning rhyme",
        "result": "the robots curved through the square and bowed to the crowd",
        "image": "a ribboned robot parade looped around the fountain while pies remained safely on their shelves",
        "lesson": "A funny clue can still be important, especially when it appears before a predictable mistake.",
    },
    {
        "purpose": "send a birthday song to a child living beyond the blue hills",
        "materials": "a balloon basket, humming wire, a moon-shaped horn, and a pocket drum",
        "foreshadow": "the horn hummed lower whenever the basket leaned toward the northern hill",
        "rhyme": "When the horn sings low, make the basket slow",
        "problem": "the birthday flyer tilted north and delivered the first verse to a herd of surprised goats",
        "turn": "heard the low hum, slowed the basket with a rope, and balanced the birthday drum beneath the seat",
        "result": "the song crossed the hills and arrived at the right window",
        "image": "the birthday melody floated through the window as the moon-shaped horn gleamed in the evening sky",
        "lesson": "Foreshadowing gives careful helpers a chance to notice danger before it becomes a disaster.",
    },
    {
        "purpose": "water the village gardens without soaking the gardeners",
        "materials": "a brass cloud tank, turnip-shaped valves, a windmill pump, and a blue umbrella",
        "foreshadow": "the blue umbrella trembled whenever the pressure grew too high",
        "rhyme": "When the umbrella quakes, open the lakes",
        "problem": "the machine shot a fountain straight upward, and one cabbage received a hat of water",
        "turn": "watched the trembling umbrella, opened the side channels, and lowered the pump with a careful crank",
        "result": "the gardens received gentle rain while the gardeners kept their shoes dry",
        "image": "tiny silver streams watered the rows as the invention's umbrella rested peacefully above the cabbages",
        "lesson": "A warning is a gift when it helps people release pressure before anything breaks.",
    },
    {
        "purpose": "make a moonlight map for travelers crossing the valley",
        "materials": "glow paint, a spinning table, a star lens, and a box of chalk gears",
        "foreshadow": "the star lens blinked twice whenever the map table turned too fast",
        "rhyme": "When stars blink twice, turn the gears nice",
        "problem": "the map spun so fast that the river appeared beside the mountain and the mountain appeared in the soup",
        "turn": "slowed the table after the double blink, tightened the chalk gears, and checked each glowing path by hand",
        "result": "the map showed the safe road beneath the moon",
        "image": "a silver road shone across the finished map while real travelers followed it home",
        "lesson": "When a small sign repeats, it deserves attention before a larger mistake follows.",
    },
    {
        "purpose": "lift a giant picnic basket to the village fair",
        "materials": "silk sails, a pulley tower, lemon-yellow rope, and a sandwich bell",
        "foreshadow": "the sandwich bell rang whenever the basket leaned toward the old oak",
        "rhyme": "When the sandwich rings, pull the yellow strings",
        "problem": "the basket swung toward the oak and nearly delivered lunch to a squirrel convention",
        "turn": "heard the bell, pulled the yellow ropes, and shifted the pulley away from the tree",
        "result": "the basket landed in the fairground with every sandwich still inside",
        "image": "the giant basket settled beneath the fair banner while squirrels watched from a respectful distance",
        "lesson": "A repeated signal can guide a brave correction before a silly problem grows teeth.",
    },
    {
        "purpose": "polish the village statue with a cloud-powered brush",
        "materials": "soft bristles, a storm jar, a silver crank, and four rubber boots",
        "foreshadow": "the storm jar rattled whenever the brush pressed too hard",
        "rhyme": "When the jar rattles round, lift the brush from the ground",
        "problem": "the brush scrubbed the statue's nose so fiercely that the nose began to shine like a second sun",
        "turn": "listened to the rattling jar, lifted the brush, and changed the crank to its gentle setting",
        "result": "the statue gleamed without losing its proper nose",
        "image": "the polished statue smiled beneath a cloud that rumbled politely instead of shouting",
        "lesson": "The best inventor does not merely build boldly; the best inventor also notices when to ease off.",
    ),
]

DIALOGUES = [
    '"The squeak is speaking before the trouble does," said {helper}. "Let us listen."',
    '"A warning can be tiny and still be true," {inventor} replied.',
    '"Do we need a bigger engine?" asked {inventor}.',
    '"Not bigger," said {helper}. "We need to understand the clue we already have."',
    '"If the rhyme predicts the wobble, the rhyme can help us stop it," said {inventor}.',
    '"Then let us test the words before we test the rooftops," {helper} said.',
    '"I built the machine, but you noticed its secret," said {inventor}.',
    '"Good inventions have room for two pairs of eyes," {helper} answered.',
    '"Should we hurry?" asked {inventor}.',
    '"Only after the warning tells us where to go," said {helper}.',
]

ENDINGS = [
    "The villagers applauded so loudly that a nearby mountain applauded back.",
    "From that day forward, the inventor wrote every warning in rhyme and every rhyme beside a wrench.",
    "The machine returned to the workshop, where its little wheel squeaked proudly whenever anyone listened.",
    "Even the clouds leaned closer, hoping to learn the next verse.",
    "That evening, the village children played the rhyme on spoons, boots, and one very patient pumpkin.",
    "The tale grew taller with every telling, but the useful clue stayed exactly the same.",
    "Nobody called the invention perfect, but everyone called it ready, which was much better.",
    "And so the workshop settled down, except for one bell that rang whenever it remembered the adventure.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A tall tale about an inventor, a rhyme, and a foreshadowed machine."
    )
    parser.add_argument("--inventor-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--invention-name", default="The Rhyme Flyer")
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
    inventor = args.inventor_name or rng.choice(INVENTOR_NAMES)
    helper = args.helper_name or rng.choice(HELPER_NAMES)
    if inventor == helper:
        raise StoryError("inventor-name and helper-name must be different people")
    return StoryParams(
        inventor_name=inventor,
        helper_name=helper,
        invention_name=args.invention_name or "The Rhyme Flyer",
        scenario=rng.randrange(len(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    if not params.inventor_name.strip():
        raise StoryError("inventor-name cannot be empty")
    if not params.helper_name.strip():
        raise StoryError("helper-name cannot be empty")
    if params.inventor_name == params.helper_name:
        raise StoryError("the inventor and helper must have different names")
    if not params.invention_name.strip():
        raise StoryError("invention-name cannot be empty")

    world = World(Workshop())
    inventor_type = "girl" if params.inventor_name in GIRL_NAMES else "boy"
    helper_type = "girl" if params.helper_name in GIRL_NAMES else "boy"
    inventor = world.add(
        Entity(
            id="Inventor",
            kind="character",
            type=inventor_type,
            label=params.inventor_name,
            memes={"curiosity": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label=params.helper_name,
            memes={"attention": 1.0},
        )
    )
    machine = world.add(
        Entity(
            id="Machine",
            type="invention",
            label=params.invention_name,
            owner="Inventor",
            meters={"unfinished": 1.0},
        )
    )
    world.facts.update(inventor=inventor, helper=helper, machine=machine, params=params)
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    inventor: Entity = world.get("Inventor")
    helper: Entity = world.get("Helper")
    machine: Entity = world.get("Machine")
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]
    world.facts["scenario"] = scenario

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"There lived an inventor named {inventor.label}, whose workshop stood so high that "
        f"the chimney smoke sometimes returned wearing snow. {inventor.label} had built "
        f"{machine.label}, a marvelous machine made from {scenario['materials']}."
    )
    world.say(
        f"The invention was meant to {scenario['purpose']}, and its first test would begin "
        f"when the valley clock struck twelve."
    )

    world.para()
    inventor.memes["pride"] = 1.0
    helper.memes["attention"] = 2.0
    world.say(
        f"Before the test, {scenario['foreshadow']}. "
        f"{helper.label} wrote a rhyme on the workbench: "
        f'"{scenario["rhyme"]}"'
    )
    world.say(
        "That was foreshadowing, though nobody used such a long word at breakfast. "
        "It simply meant that a small clue had arrived before the large trouble."
    )
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(
        inventor=inventor.label,
        helper=helper.label,
    ))
    world.say(
        f"Still, the machine launched with a puff, a clang, and enough confidence "
        f"to make the workshop door salute."
    )

    world.para()
    machine.meters["unstable"] = 1.0
    world.say(f"Then {scenario['problem']}.")
    world.say(
        f"The villagers shouted advice in seventeen directions, but {inventor.label} "
        f"remembered the early clue instead of guessing louder."
    )
    world.say(
        f"{inventor.label} called, 'Read the rhyme!' and {helper.label} answered, "
        f'"The warning tells us what to do!"'
    )
    world.say(
        f"Together, they {scenario['turn']}. The machine steadied, the wild motion stopped, "
        f"and the invention became useful instead of merely impressive."
    )
    machine.meters["unstable"] = 0.0
    machine.meters["repaired"] = 1.0
    inventor.memes["humility"] = 1.0
    helper.memes["trust"] = 1.0

    world.para()
    world.say(f"As a result, {scenario['result']}.")
    world.say(f"In the final sight, {scenario['image']}.")
    world.say(scenario["lesson"])
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        resolved=True,
        foreshadow=scenario["foreshadow"],
        rhyme=scenario["rhyme"],
        problem=scenario["problem"],
        turn=scenario["turn"],
        result=scenario["result"],
        ending_image=scenario["image"],
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a tall tale for children about inventor {params.inventor_name} and helper {params.helper_name}.",
        f"Tell a story about {params.invention_name}, a machine built to {scenario['purpose']}.",
        f"Use this rhyme as foreshadowing: {scenario['rhyme']}. Let the clue help repair the invention.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question="Who built the marvelous machine?",
            answer=f"{params.inventor_name}, the inventor, built {params.invention_name} from {scenario['materials']}.",
        ),
        QAItem(
            question="What was the rhyme in the story?",
            answer=f"The rhyme was, “{scenario['rhyme']}” It warned the characters what to notice before the machine caused trouble.",
        ),
        QAItem(
            question="How did the early clue foreshadow the problem?",
            answer=f"Before the trouble, {scenario['foreshadow']}. Later, {scenario['problem']}, so the early clue showed what kind of danger was coming.",
        ),
        QAItem(
            question=f"How did {params.inventor_name} and {params.helper_name} fix the invention?",
            answer=f"They remembered the rhyme and then {scenario['turn']}. This made the machine steady and useful.",
        ),
        QAItem(
            question="What proved that the story ended well?",
            answer=f"The ending showed that {scenario['image']}. The invention completed its purpose after the warning was understood.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inventor?",
            answer="An inventor is a person who designs or builds something new to solve a problem or do a useful job.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a group of words or lines that share similar ending sounds.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue that hints at something important that will happen later.",
        ),
        QAItem(
            question="What makes a tall tale?",
            answer="A tall tale uses playful exaggeration, surprising events, and larger-than-life details while still giving the story a clear problem and ending.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(details) if details else '(quiet)'}")
    return "\n".join(lines)


ASP_RULES = r"""
inventor(inventor).
helper(helper).
machine(machine).
clue_present :- inventor(inventor), helper(helper).
unstable(machine) :- clue_present, machine(machine).
rhyme_warning :- clue_present.
repaired(machine) :- rhyme_warning, unstable(machine).
successful(machine) :- repaired(machine).
#show clue_present/0.
#show rhyme_warning/0.
#show unstable/1.
#show repaired/1.
#show successful/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("inventor", "inventor"),
            asp.fact("helper", "helper"),
            asp.fact("machine", "machine"),
        ]
    )


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    names = {(symbol.name, len(symbol.arguments)) for symbol in model}
    required = {
        ("clue_present", 0),
        ("rhyme_warning", 0),
        ("unstable", 1),
        ("repaired", 1),
        ("successful", 1),
    }
    if not required.issubset(names):
        raise StoryError("ASP twin did not derive every expected inventor-story state")
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            raise StoryError("generated verification story did not resolve")
        if "rhyme" not in sample.world.facts or "foreshadow" not in sample.world.facts:
            raise StoryError("generated story omitted rhyme or foreshadowing facts")
    print("OK: ASP/Python parity and generated story checks passed.")
    return 0


CURATED = [
    StoryParams(
        inventor_name="Luna",
        helper_name="Jun",
        invention_name="The Rhyme Flyer",
        scenario=0,
        opening=0,
        dialogue=0,
        ending=0,
    ),
    StoryParams(
        inventor_name="Milo",
        helper_name="Mara",
        invention_name="The Cloud Kettle",
        scenario=1,
        opening=3,
        dialogue=4,
        ending=5,
    ),
    StoryParams(
        inventor_name="Tessa",
        helper_name="Otto",
        invention_name="The Moon Map",
        scenario=5,
        opening=6,
        dialogue=7,
        ending=2,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        import asp

        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(target * 50, 50):
            current_seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(current_seed))
            params.seed = current_seed
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
        header = ""
        if args.all:
            header = f"### {sample.params.inventor_name} / {sample.params.helper_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
