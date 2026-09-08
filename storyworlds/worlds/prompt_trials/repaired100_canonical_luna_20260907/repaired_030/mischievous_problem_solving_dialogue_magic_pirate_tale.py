#!/usr/bin/env python3
"""
A child-facing pirate tale about mischievous magic, careful problem solving,
and a conversation that changes what the crew chooses to do.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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


@dataclass
class StoryParams:
    captain: str
    deckhand: str
    parrot: str
    spell: str
    problem: str
    solution: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Spell:
    name: str
    effect: str
    danger: str
    clue: str


@dataclass(frozen=True)
class Problem:
    trouble: str
    sign: str
    consequence: str
    object_name: str


SPELLS = {
    "whistling_compass": Spell(
        name="the Whistling Compass",
        effect="make a silver compass whistle whenever someone nearby tells the truth",
        danger="it also spins wildly when a greedy wish is spoken",
        clue="The compass whistled once, then pointed toward the dark clouds.",
    ),
    "moonlit_rope": Spell(
        name="the Moonlit Rope",
        effect="tie itself to anything that needs rescuing",
        danger="it knots itself into a giant loop when someone gives an order without listening",
        clue="A pale rope slipped from the mast and curled toward the broken rail.",
    ),
    "talking_map": Spell(
        name="the Talking Map",
        effect="draw a bright path toward whatever is lost",
        danger="it scribbles nonsense when a sailor hides an important fact",
        clue="The ink map coughed and drew a tiny arrow toward the cargo hold.",
    ),
    "stormy_lantern": Spell(
        name="the Stormy Lantern",
        effect="shine through fog and reveal safe water",
        danger="it flashes purple whenever someone rushes without a plan",
        clue="The lantern blinked three times at the rocks ahead.",
    ),
}


PROBLEMS = {
    "stolen_wind": Problem(
        trouble="a mischievous wind sprite stole the ship's steady breeze",
        sign="the sails sagged like sleepy blankets",
        consequence="The ship drifted toward a reef shaped like a dragon's tooth",
        object_name="wind sprite",
    ),
    "backward_anchor": Problem(
        trouble="a mischievous anchor spell pulled the anchor upward instead of down",
        sign="the anchor rose and waved above the waves",
        consequence="The ship could not hold still beside the floating market",
        object_name="anchor spell",
    ),
    "vanishing_cargo": Problem(
        trouble="a mischievous magic crab made the treasure crates vanish one by one",
        sign="the last crate disappeared with a tiny pop",
        consequence="The crew might lose the medicine meant for a distant island",
        object_name="magic crab",
    ),
    "sleeping_lighthouse": Problem(
        trouble="a mischievous moonbeam put the lighthouse to sleep",
        sign="the lighthouse winked and went dark",
        consequence="Ships below could not see the safe channel between the rocks",
        object_name="moonbeam",
    ),
    "singing_cannon": Problem(
        trouble="a mischievous song spell made the cannon sing instead of fire",
        sign="the cannon sang a very high note",
        consequence="The crew could not send a rescue line to a stranded boat",
        object_name="song spell",
    ),
    "upside_down_ocean": Problem(
        trouble="a mischievous wave charm turned the sea upside down",
        sign="fish floated above the mast while clouds splashed below",
        consequence="The ship's crew could not tell sky from water",
        object_name="wave charm",
    ),
}


ENDING_IMAGES = {
    "sunrise": (
        "At sunrise, the repaired ship sailed across a calm orange sea",
        "The crew cheered, but Captain Mira thanked the smallest helper first.",
    ),
    "rainbow": (
        "A rainbow curled over the mast and shone on the freshly mended deck",
        "Even the magic laughed softly, as if it had learned a better trick.",
    ),
    "safe_harbor": (
        "By evening, the ship slipped into a bright harbor where lanterns bobbed like stars",
        "The crew tied up together and left room for every voice at the next adventure.",
    ),
    "blue_moon": (
        "Under a blue moon, the ship glided past the reef with every sail singing",
        "No one called the solution lucky, because they had worked it out together.",
    ),
    "feast": (
        "The cook spread a warm feast across the deck beneath fluttering pirate flags",
        "The mischievous magic crab received the first biscuit after returning what it had hidden.",
    ),
}


CAPTAINS = ["Captain Mira", "Captain Sol", "Captain Pippa", "Captain Rowan"]
DECKHANDS = ["Nico", "Tavi", "Jun", "Rafi", "Lulu", "Bram"]
PARROTS = ["Pepper", "Coco", "Sprig", "Bluebeak"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mischievous magic pirate tale storyworld.")
    parser.add_argument("--captain")
    parser.add_argument("--deckhand")
    parser.add_argument("--parrot")
    parser.add_argument("--spell", choices=SPELLS)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=("listen", "map", "divide", "slow_down"))
    parser.add_argument("--ending", choices=ENDING_IMAGES)
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
    captain = args.captain or rng.choice(CAPTAINS)
    deckhand = args.deckhand or rng.choice([x for x in DECKHANDS if x != captain])
    parrot = args.parrot or rng.choice(PARROTS)
    solution = args.solution or rng.choice(("listen", "map", "divide", "slow_down"))
    return StoryParams(
        captain=captain,
        deckhand=deckhand,
        parrot=parrot,
        spell=args.spell or rng.choice(tuple(SPELLS)),
        problem=args.problem or rng.choice(tuple(PROBLEMS)),
        solution=solution,
        ending=args.ending or rng.choice(tuple(ENDING_IMAGES)),
    )


def solve_text(choice: str, captain: str, deckhand: str, parrot: str) -> str:
    if choice == "listen":
        return (
            f"{captain} asked {deckhand} and {parrot} to describe what they had noticed. "
            f"Together they heard the quiet clue beneath the noisy magic."
        )
    if choice == "map":
        return (
            f"{deckhand} drew the danger as a little island on the deck, while {captain} "
            f"used the map to mark a safe route around it."
        )
    if choice == "divide":
        return (
            f"{captain} gave one small task to {deckhand}, another to the parrot, and kept "
            f"the final task for themself."
        )
    return (
        f"The captain lowered their voice, slowed every hand, and counted three careful "
        f"breaths before touching the magic."
    )


def tell(params: StoryParams) -> World:
    spell = SPELLS[params.spell]
    problem = PROBLEMS[params.problem]
    ending = ENDING_IMAGES[params.ending]

    world = World()
    captain = world.add(Entity("captain", "character", params.captain, "quarterdeck"))
    deckhand = world.add(Entity("deckhand", "character", params.deckhand, "main deck"))
    parrot = world.add(Entity("parrot", "animal", params.parrot, "mast"))
    magic = world.add(Entity("magic", "artifact", spell.name, "captain's cabin"))
    trouble = world.add(Entity("trouble", "creature", problem.object_name, "main deck"))

    world.facts.update(
        captain=captain,
        deckhand=deckhand,
        parrot=parrot,
        magic=magic,
        trouble=trouble,
        spell=spell,
        problem=problem,
        ending=ending,
        solution=params.solution,
    )

    world.say(
        f"Once, aboard the little pirate ship Starling, {params.captain} sailed with "
        f"{params.deckhand} and a mischievous parrot named {params.parrot}."
    )
    world.say(
        f"In the captain's cabin lay {spell.name}, a piece of magic that could {spell.effect}."
    )
    world.say(f"But one bright morning, {problem.trouble}.")
    world.say(f"The first sign was simple: {problem.sign}.")
    world.para()

    world.entities["trouble"].memes["mischief"] = 1
    world.entities["captain"].memes["worry"] = 1
    world.entities["deckhand"].meters["problem_solving"] = 1
    world.say(f"{problem.consequence}.")
    world.say(f"{spell.clue}")
    world.say(
        f"{params.captain} grabbed the magic, but {params.deckhand} called, "
        f'"Wait! What does the clue mean?"'
    )
    world.say(
        f'"It means we must not chase the trick blindly," said {params.captain}. '
        f'"Tell me what you see."'
    )
    world.say(
        f'"I see the {problem.object_name} watching the {spell.name.lower()}," '
        f"answered {params.deckhand}."
    )
    world.say(
        f'The parrot squawked, "{params.parrot} sees the loose bell!" and pointed with one wing.'
    )
    world.para()

    world.entities["captain"].memes["listening"] = 1
    world.entities["deckhand"].memes["confidence"] = 1
    world.say(
        f"The crew chose to {params.solution.replace('_', ' ')} instead of blaming the magic."
    )
    world.say(solve_text(params.solution, params.captain, params.deckhand, params.parrot))
    world.say(
        f'Then {params.deckhand} said, "If we ring the bell only when the sea is clear, '
        f"the magic will have to show us the safe moment.\""
    )
    world.say(
        f'"A clever plan," said {params.captain}. "And we will test it slowly."'
    )
    world.say(
        f"The bell rang once. The {problem.object_name} blinked. "
        f"The magic stopped its mischievous dance."
    )
    world.entities["trouble"].memes["mischief"] = 0
    world.entities["captain"].memes["trust"] = 1
    world.entities["deckhand"].memes["confidence"] = 2
    world.facts["resolved"] = True
    world.facts["changed_fact"] = f"The {problem.object_name} was guided away without harming the ship."
    world.para()

    world.say(
        f"{params.captain} smiled and said, \"A problem is smaller when every good clue gets heard.\""
    )
    world.say(f"{ending[0]}.")
    world.say(ending[1])
    return world


def generation_prompts(world: World) -> list[str]:
    problem = world.facts["problem"]
    spell = world.facts["spell"]
    return [
        f"Tell a pirate tale about {problem.trouble}.",
        f"Use dialogue and problem solving to control {spell.name}.",
        "Include mischievous magic, a clear turning point, and a hopeful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain = world.facts["captain"].label
    deckhand = world.facts["deckhand"].label
    problem: Problem = world.facts["problem"]
    spell: Spell = world.facts["spell"]
    solution = str(world.facts["solution"]).replace("_", " ")
    return [
        QAItem(
            question="Who faced the magical trouble?",
            answer=f"{captain}, {deckhand}, and the parrot faced it together aboard the pirate ship Starling.",
        ),
        QAItem(
            question="What was the first sign of the problem?",
            answer=f"The first sign was that {problem.sign}. This warned the crew before {problem.consequence}.",
        ),
        QAItem(
            question="How did the crew solve the problem?",
            answer=f"They chose to {solution}, listened to the clue from {spell.name}, and tested their plan slowly instead of chasing the mischievous magic.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The {problem.object_name} was guided away without harming the ship, and the crew learned that every good clue deserves to be heard.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a sailing vessel used by a pirate crew to travel across the sea.",
        ),
        QAItem(
            question="Why is dialogue useful during a problem?",
            answer="Dialogue lets people share clues, correct mistakes, and choose a safer plan together.",
        ),
        QAItem(
            question="What is magic in this storyworld?",
            answer="Magic is a playful force that can change objects and events, but it must be handled with care and understanding.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    lines.append(f"  changed_fact={world.facts.get('changed_fact', '')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(starling).
feature(problem_solving).
feature(dialogue).
feature(magic).
valid_story :- place(starling), feature(problem_solving), feature(dialogue), feature(magic).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "starling"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "magic"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    okay = any(symbol.name == "valid_story" for symbol in (models[0] if models else []))
    if okay:
        print("OK: ASP confirms the pirate storyworld features.")
        return 0
    print("ASP verification failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        for prompt in sample.prompts:
            print(f"\n[Prompt] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print("\n" + show_qa_item(item))


CURATED = [
    StoryParams(
        captain="Captain Mira",
        deckhand="Nico",
        parrot="Pepper",
        spell="whistling_compass",
        problem="stolen_wind",
        solution="listen",
        ending="sunrise",
    ),
    StoryParams(
        captain="Captain Sol",
        deckhand="Tavi",
        parrot="Coco",
        spell="moonlit_rope",
        problem="backward_anchor",
        solution="slow_down",
        ending="safe_harbor",
    ),
    StoryParams(
        captain="Captain Pippa",
        deckhand="Jun",
        parrot="Sprig",
        spell="talking_map",
        problem="vanishing_cargo",
        solution="divide",
        ending="feast",
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
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
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
