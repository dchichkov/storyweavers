#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a panda, a herald, and a hopping message.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=lambda: {"listen", "search", "follow", "repair"})


@dataclass
class StoryParams:
    panda_name: str
    herald_name: str
    hopper_name: str
    setting: int = 0
    clue: int = 0
    plan: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    place: str
    signal: str
    destination: str
    obstacle: str
    repair: str
    final_image: str


SCENARIOS = [
    Scenario(
        "the moonlit bamboo grove",
        "three soft thumps beyond the sleeping bamboo",
        "the little hill above the pond",
        "a silver bell tangled in a low branch",
        "untangled the bell and tied it to the moon gate",
        "the bell chimed once, and the pond held a bright round moon",
    ),
    Scenario(
        "the quiet hilltop garden",
        "a tiny hop and a rustle behind the lavender",
        "the old sundial",
        "a blue ribbon caught beneath a garden stone",
        "freed the ribbon and fastened it to the message staff",
        "the ribbon fluttered gently while the stars blinked awake",
    ),
    Scenario(
        "the sleepy forest station",
        "a faint tap from the dark end of the path",
        "the lantern tower",
        "a folded bedtime note wedged inside a hollow log",
        "slid the note free with a smooth willow twig",
        "the lantern glowed above the path like a warm little star",
    ),
    Scenario(
        "the cloud-white mountain porch",
        "a quick hop followed by a worried squeak",
        "the nest beneath the bell tower",
        "a fallen pinecone blocking the narrow bridge",
        "rolled the pinecone aside and tested each bridge plank",
        "the nest rested safely under the tower as clouds drifted past",
    ),
]

CLUES = [
    "a line of pearly footprints crossed the moss",
    "one loose feather trembled beside the path",
    "a bright thread shone between two stones",
    "three leaves lay in a careful little row",
]

PLANS = [
    ("listen first, mark each clue, and change only one thing at a time",
     "they placed a pebble beside every clue they had checked"),
    ("walk together and let the herald call the path while the panda examined it",
     "they traded jobs halfway so neither one had to solve the puzzle alone"),
    ("count the hops, compare the sounds, and return to every doubtful spot",
     "they repeated the count until the pattern made sense"),
]

ENDINGS = [
    "The panda tucked the lesson into his heart: a calm question can be stronger than a frightened guess.",
    "The herald smiled, knowing that careful friends can turn suspense into a path home.",
    "The hopper gave one last gentle hop, and everyone understood that patient solving brings quiet back.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


def propagate(world: World) -> None:
    panda = world.entities["Panda"]
    herald = world.entities["Herald"]
    hopper = world.entities["Hopper"]
    if panda.memes.get("curious", 0) and "curiosity" not in world.fired:
        world.fired.add("curiosity")
        world.say("The panda listened instead of running. A mystery was still a question, not yet a danger.")
    if herald.memes.get("clear_voice", 0) and hopper.meters.get("hops", 0) >= 2 and "pattern" not in world.fired:
        world.fired.add("pattern")
        world.say("The herald called the count aloud, and the hopper's jumps revealed a pattern in the dark.")
    if panda.meters.get("clues", 0) >= 3 and herald.memes.get("teamwork", 0) and "solution" not in world.fired:
        world.fired.add("solution")
        world.say("Three clues joined together like pieces of a small puzzle. Now the friends could solve the problem.")


def build_story(params: StoryParams) -> World:
    if not params.panda_name.strip() or not params.herald_name.strip() or not params.hopper_name.strip():
        raise StoryError("Names must not be empty.")
    scenario = SCENARIOS[params.setting % len(SCENARIOS)]
    clue = CLUES[params.clue % len(CLUES)]
    plan = PLANS[params.plan % len(PLANS)]
    ending = ENDINGS[params.ending % len(ENDINGS)]
    world = World(Setting(scenario.place))

    panda = world.add(Entity("Panda", "character", "panda", params.panda_name))
    herald = world.add(Entity("Herald", "character", "herald", params.herald_name))
    hopper = world.add(Entity("Hopper", "character", "hopper", params.hopper_name))

    world.facts.update(
        panda=panda,
        herald=herald,
        hopper=hopper,
        scenario=scenario,
        clue=clue,
        plan=plan,
        ending=ending,
    )

    world.say(
        f"At bedtime, {panda.label} was settling down in {scenario.place} when "
        f"{scenario.signal} drifted through the dark."
    )
    panda.memes["curious"] = 1
    propagate(world)
    world.say(f'"Did you hear that?" whispered {panda.label}. "I did," said {herald.label}, holding the message staff close.')
    world.para()

    world.say(
        f"Then {hopper.label} appeared with a worried little hop. "
        f'"The night message must reach {scenario.destination}," said the herald. '
        f'"Let us {plan[0]}."'
    )
    herald.memes["clear_voice"] = 1
    herald.memes["teamwork"] = 1
    hopper.meters["hops"] = 1
    world.say(
        f'"I can hop ahead," said {hopper.label}. "And I can look low," said {panda.label}. '
        f'"Then I will listen for the safe way," said {herald.label}.'
    )
    world.para()

    world.say(f"{hopper.label} made a careful hop. {panda.label} found {clue}.")
    hopper.meters["hops"] = 2
    panda.meters["clues"] = 1
    propagate(world)
    world.say(f"The suspense grew when they reached the narrowest part of the path: {scenario.obstacle}.")
    world.say(f'"Should we hurry?" asked {hopper.label}. "No," said {panda.label}. "A hurry can hide a clue."')
    world.para()

    world.say(f"They followed their plan. {plan[1].capitalize()}.")
    panda.meters["clues"] = 2
    hopper.meters["hops"] = 3
    world.say(f"At the next bend, the herald heard the same soft sound, and {panda.label} noticed {clue}.")
    panda.meters["clues"] = 3
    propagate(world)
    world.say(f"Together, they discovered the cause: {scenario.obstacle}.")
    world.say(
        f'"Now we know what to do," said {herald.label}. They {scenario.repair}. '
        f"The mysterious sound became a friendly sound again."
    )
    world.para()

    world.say(
        f"They carried the bedtime message to {scenario.destination}. "
        f"When they returned, {scenario.final_image.capitalize()}."
    )
    world.say(ending)
    world.facts["lesson"] = "Careful questions, shared clues, and teamwork can turn suspense into a solution."
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle bedtime story about {f['panda'].label}, {f['herald'].label}, and {f['hopper'].label} in {f['scenario'].place}.",
        "Tell a suspenseful but safe story in which friends solve a nighttime problem by sharing clues.",
        "Write a child-friendly problem-solving tale with a panda, a herald, and a hopper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    panda = f["panda"]
    herald = f["herald"]
    hopper = f["hopper"]
    scenario = f["scenario"]
    return [
        QAItem(
            f"Why did {panda.label} feel suspense at bedtime?",
            f"{panda.label} heard {scenario.signal} in {scenario.place} and did not yet know what caused it.",
        ),
        QAItem(
            f"How did {panda.label}, {herald.label}, and {hopper.label} solve the problem?",
            f"They listened carefully, followed clues together, counted the hopper's jumps, and discovered {scenario.obstacle}. Then they {scenario.repair}.",
        ),
        QAItem(
            f"What did the herald do to help?",
            f"{herald.label} used a clear voice to call the path and helped the friends follow their plan instead of hurrying.",
        ),
        QAItem(
            "What lesson did the friends learn?",
            f"They learned that {f['lesson'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a panda?", "A panda is a bear-like animal with black-and-white fur that often eats bamboo."),
        QAItem("What is a herald?", "A herald is someone who announces news or carries an important message."),
        QAItem("What is a hopper?", "A hopper is a creature or object that moves by hopping."),
        QAItem("What is suspense?", "Suspense is the feeling of waiting to learn what will happen next."),
        QAItem("What is problem solving?", "Problem solving means noticing a difficulty, examining clues, and choosing a helpful answer."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("topic", "panda"),
        asp.fact("topic", "herald"),
        asp.fact("topic", "hopper"),
        asp.fact("feature", "suspense"),
        asp.fact("feature", "problem_solving"),
        asp.fact("style", "bedtime_story"),
        asp.fact("affords", "night_path", "listen"),
        asp.fact("affords", "night_path", "search"),
        asp.fact("affords", "night_path", "repair"),
    ])


ASP_RULES = r"""
topic(panda).
topic(herald).
topic(hopper).
feature(suspense).
feature(problem_solving).
style(bedtime_story).
needs_clues(problem_solving).
needs_teamwork(problem_solving).
safe_suspense :- feature(suspense), needs_clues(problem_solving).
story_ok :- topic(panda), topic(herald), topic(hopper), safe_suspense, style(bedtime_story).
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    if any(symbol.name == "story_ok" for symbol in model):
        print("OK: ASP twin recognizes the panda bedtime story world.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Panda, herald, and hopper bedtime storyworld.")
    parser.add_argument("--panda-name")
    parser.add_argument("--herald-name")
    parser.add_argument("--hopper-name")
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


PANDA_NAMES = ["Luna", "Bao", "Ming", "Pip", "Nori"]
HERALD_NAMES = ["Mira", "Tess", "Orin", "Wren", "Sage"]
HOPPER_NAMES = ["Bibi", "Pogo", "Tumble", "Hops", "Kiko"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        panda_name=args.panda_name or rng.choice(PANDA_NAMES),
        herald_name=args.herald_name or rng.choice(HERALD_NAMES),
        hopper_name=args.hopper_name or rng.choice(HOPPER_NAMES),
        setting=rng.randrange(len(SCENARIOS)),
        clue=rng.randrange(len(CLUES)),
        plan=rng.randrange(len(PLANS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i in range(len(SCENARIOS)):
            params = StoryParams(
                panda_name="Luna",
                herald_name="Mira",
                hopper_name="Pogo",
                setting=i,
                clue=i % len(CLUES),
                plan=i % len(PLANS),
                ending=i % len(ENDINGS),
                seed=seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            params = resolve_params(args, random.Random(seed + index))
            params.seed = seed + index
            index += 1
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
