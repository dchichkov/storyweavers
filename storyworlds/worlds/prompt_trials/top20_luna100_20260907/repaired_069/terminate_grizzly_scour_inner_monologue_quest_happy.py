#!/usr/bin/env python3
"""A child-friendly superhero quest about a grizzly, a careful scour, and a happy ending."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    grizzly: str = "Bruno"
    place: str = "the North Star City"
    trial: int = 0
    opening: int = 0
    thought: int = 0
    dialogue: int = 0
    ending: int = 0


HEROES = ["Luna", "Comet", "Nova", "Beacon", "Sky"]
GRIZZLIES = ["Bruno", "Hazel", "Marlow", "Tundra"]
PLACES = ["the North Star City", "the Moonlit Harbor", "the Silverwood Town", "the Cloudbridge City"]

TRIALS = [
    {
        "title": "the clocktower rescue",
        "problem": "A storm twisted the clocktower's signal wires, and the city's emergency bell could not ring.",
        "clue": "Luna noticed that one bright wire still carried a tiny pulse whenever the moon flashed.",
        "action": "She followed the pulse, while the grizzly held the ladder steady, and joined the loose wires with a silver clasp.",
        "result": "The bell rang across the rooftops, guiding every lost child home before the rain grew fierce.",
        "object": "signal wires",
        "lesson": "A hero searches carefully before making a risky move.",
        "ending": "At sunrise, the clocktower shone with a new silver star beside its bell.",
    },
    {
        "title": "the river of runaway lanterns",
        "problem": "Festival lanterns had slipped from their ropes and floated toward a dark waterfall.",
        "clue": "Luna saw that a line of lily pads formed a safe curve across the slow part of the river.",
        "action": "She sent a gentle wind along that curve while the grizzly used a branch to guide the lanterns toward shore.",
        "result": "The lanterns returned safely, and their warm lights showed the way to the festival.",
        "object": "festival lanterns",
        "lesson": "A calm plan can redirect trouble without hurting anyone.",
        "ending": "The rescued lanterns floated above the festival like a friendly second sky.",
    },
    {
        "title": "the shadow under the bridge",
        "problem": "A huge shadow blocked the bridge, and travelers feared a monster had arrived.",
        "clue": "Luna discovered that the shadow came from a fallen sail stretched between two towers.",
        "action": "She asked the grizzly to scour the riverbank for safe knots, then lowered the sail with a careful pull.",
        "result": "The bridge opened again, and the frightened travelers laughed at the harmless sail.",
        "object": "fallen sail",
        "lesson": "Looking for the true cause can turn fear into understanding.",
        "ending": "The old sail became a bright picnic canopy beside the bridge.",
    },
    {
        "title": "the silent rescue robot",
        "problem": "The town's rescue robot stopped before it could carry medicine to the hill clinic.",
        "clue": "Luna heard a soft click beneath its muddy wheel and found a pebble wedged in the gear.",
        "action": "She had the grizzly scour the mud away with a pine branch, then freed the gear without breaking it.",
        "result": "The robot carried the medicine uphill, and the clinic's patients received help in time.",
        "object": "rescue robot",
        "lesson": "Small careful work can restart a very important mission.",
        "ending": "The robot blinked a happy blue light beside the clinic door.",
    },
]

OPENINGS = [
    "{hero} watched over {place} from a rooftop, where every streetlight looked like a tiny star.",
    "At dawn, {hero} zipped above {place} and heard a worried bell below.",
    "The people of {place} knew that when a silver streak crossed the sky, their superhero was near.",
    "A bright quest began when {hero} found a frightened crowd gathering at the edge of {place}.",
]

THOUGHTS = [
    "I could rush in and use all my power, Luna thought, but a true hero must first learn what is really wrong.",
    "Luna's cape tugged in the wind. I will scour the clues before I choose my strongest move, she thought.",
    "The danger looked enormous. Still, Luna told herself, One careful step can protect more people than one wild leap.",
    "Luna felt nervous, but her inner voice answered, A quest is not about looking fearless; it is about helping wisely.",
]

DIALOGUES = [
    "“Should we terminate the danger with one giant blast?” the grizzly asked. “No,” said Luna. “We will terminate the trouble, not damage the town.”",
    "“I am big enough to push through,” said the grizzly. Luna replied, “And I am patient enough to scour for the safe path. We need both strengths.”",
    "“What do you see?” asked the grizzly. “A clue,” said Luna. “Help me test it before we act.”",
    "“The crowd is afraid,” said the grizzly. Luna answered, “Then our first job is to discover the truth and make them feel safe.”",
]

ENDINGS = [
    "The people cheered, but Luna simply smiled as the grizzly waved from the shining street.",
    "That evening, children drew the two heroes together: one with a silver cape and one with a warm, shaggy grin.",
    "The grizzly placed a small star on Luna's cape, and Luna thanked him for being part of the quest.",
    "With the danger gone, music filled the air, and even the grizzly danced beneath the happy lights.",
]


ASP_RULES = r"""
#show quest/1.
#show solved/1.
#show happy_ending/1.

quest(Q) :- chosen_quest(Q), clue_found(Q).
solved(Q) :- quest(Q), helper_present(Q), safe_action(Q).
happy_ending(Q) :- solved(Q), people_safe(Q).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("chosen_quest", "heroic_rescue"),
            asp.fact("clue_found", "heroic_rescue"),
            asp.fact("helper_present", "heroic_rescue"),
            asp.fact("safe_action", "heroic_rescue"),
            asp.fact("people_safe", "heroic_rescue"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about Luna, a grizzly, and a careful quest."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--grizzly", choices=GRIZZLIES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--trial", type=int, choices=range(len(TRIALS)))
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        grizzly=args.grizzly or rng.choice(GRIZZLIES),
        place=args.place or rng.choice(PLACES),
        trial=args.trial if args.trial is not None else rng.randrange(len(TRIALS)),
        opening=rng.randrange(len(OPENINGS)),
        thought=rng.randrange(len(THOUGHTS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.grizzly:
        raise StoryError("The hero and grizzly must have different names.")
    if not 0 <= params.trial < len(TRIALS):
        raise StoryError("The selected quest trial is not available.")

    trial = TRIALS[params.trial]
    world = World()

    hero = world.add(
        Entity(
            id=params.hero,
            type="superhero",
            label=params.hero,
            meters={"height": 1.0, "energy": 1.0},
            memes={"courage": 1.0, "curiosity": 1.0},
        )
    )
    grizzly = world.add(
        Entity(
            id=params.grizzly,
            type="grizzly",
            label=params.grizzly,
            meters={"strength": 1.0, "warmth": 1.0},
            memes={"loyalty": 1.0, "worry": 0.4},
        )
    )

    def fill(text: str) -> str:
        return text.format(hero=hero.id, grizzly=grizzly.id, place=params.place)

    world.say(fill(OPENINGS[params.opening % len(OPENINGS)]))
    world.say(f"The quest was {trial['title']}. {trial['problem']}")
    world.say(fill(THOUGHTS[params.thought % len(THOUGHTS)]))
    world.say(fill(DIALOGUES[params.dialogue % len(DIALOGUES)]))
    world.say(f"{hero.id} and {grizzly.id} began to scour the area for a clue. {trial['clue']}")
    world.say(f"{hero.id} made a plan. {trial['action']}")
    world.say(f"The plan worked. {trial['result']}")
    hero.memes["confidence"] = 1.0
    grizzly.memes["worry"] = 0.0
    world.say(
        f"Together, {hero.id} and {grizzly.id} could terminate the danger without hurting the people they came to protect."
    )
    world.say(f"Happy ending: {trial['lesson']}")
    world.say(trial["ending"])
    world.say(fill(ENDINGS[params.ending % len(ENDINGS)]))

    world.facts.update(
        hero=hero,
        grizzly=grizzly,
        place=params.place,
        trial=trial,
        quest=trial["title"],
        clue=trial["clue"],
        solved=True,
        terminated=True,
        happy=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    grizzly = world.facts["grizzly"]
    trial = world.facts["trial"]
    return [
        f"Write a child-friendly superhero quest about {hero.id} and {grizzly.id} solving {trial['title']}.",
        f"Tell a superhero story in which {hero.id} uses an inner monologue to scour for clues before acting.",
        f"Write a story with a grizzly helper, a safe way to terminate danger, and a happy ending involving {trial['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    grizzly = world.facts["grizzly"]
    trial = world.facts["trial"]
    return [
        QAItem(
            question=f"What quest did {hero.id} and {grizzly.id} undertake?",
            answer=f"They undertook {trial['title']} in order to protect the people nearby.",
        ),
        QAItem(
            question=f"What did {hero.id} discover while scouring for clues?",
            answer=trial["clue"],
        ),
        QAItem(
            question=f"How did {grizzly.id} help?",
            answer=f"{grizzly.id} helped by using strength carefully and supporting {hero.id}'s safe plan: {trial['action']}",
        ),
        QAItem(
            question="How was the danger terminated?",
            answer=f"The danger was terminated by a careful action that solved the real problem without hurting anyone: {trial['action']}",
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"It was happy because {trial['result']} The people were safe, and the heroes finished their quest together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end or stop it.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear with strong muscles and a shaggy coat.",
        ),
        QAItem(
            question="What does scour mean in a quest?",
            answer="To scour means to search an area carefully for something.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts written as words inside the story.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the main problem has been resolved and the characters or community are safe or joyful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for number, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{number}. {prompt}")
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
        lines.append(
            f"  {entity.id} ({entity.type}) meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(
        asp_program("#show quest/1.\n#show solved/1.\n#show happy_ending/1.")
    )
    return sorted(
        set(
            asp.atoms(model, "quest")
            + asp.atoms(model, "solved")
            + asp.atoms(model, "happy_ending")
        )
    )


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show quest/1.\n#show solved/1.\n#show happy_ending/1."))
    actual = {
        ("quest", atom[0])
        for atom in asp.atoms(model, "quest")
    }
    actual.update(("solved", atom[0]) for atom in asp.atoms(model, "solved"))
    actual.update(("happy_ending", atom[0]) for atom in asp.atoms(model, "happy_ending"))
    expected = {
        ("quest", "heroic_rescue"),
        ("solved", "heroic_rescue"),
        ("happy_ending", "heroic_rescue"),
    }
    if actual != expected:
        print("MISMATCH between clingo and Python gate.")
        print("  clingo:", sorted(actual))
        print("  python:", sorted(expected))
        return 1

    sample = generate(StoryParams(seed=7))
    required = ["quest", "scour", "grizzly", "happy ending", "inner voice"]
    lowered = sample.story.lower()
    if "grizzly" not in lowered or "happy ending" not in lowered:
        print("Generated story verification failed.")
        return 1
    if not any(word in lowered for word in required[1:]):
        print("Generated story is missing required narrative language.")
        return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


CURATED = [
    StoryParams(hero="Luna", grizzly="Bruno", place="the North Star City", trial=0, opening=0, thought=0, dialogue=0, ending=0),
    StoryParams(hero="Comet", grizzly="Hazel", place="the Moonlit Harbor", trial=1, opening=1, thought=1, dialogue=1, ending=1),
    StoryParams(hero="Nova", grizzly="Marlow", place="the Silverwood Town", trial=2, opening=2, thought=2, dialogue=2, ending=2),
    StoryParams(hero="Beacon", grizzly="Tundra", place="the Cloudbridge City", trial=3, opening=3, thought=3, dialogue=3, ending=3),
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
        print(asp_program("#show quest/1.\n#show solved/1.\n#show happy_ending/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        facts = asp_valid()
        print(f"{len(facts)} ASP story-state facts")
        for fact in facts:
            print(fact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.hero}: superhero quest"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
