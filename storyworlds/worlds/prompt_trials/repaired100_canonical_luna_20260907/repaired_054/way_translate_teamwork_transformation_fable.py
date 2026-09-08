#!/usr/bin/env python3
"""A fable StoryWorld about finding a way to translate a shared idea."""

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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "the old bridge"
    first_name: str = "Luna"
    second_name: str = "Pip"
    message: str = "the river is rising"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    obstacle: str
    failed: str
    clue: str
    plan: str
    jobs: tuple[str, str]
    result: str
    lesson: str
    ending: str


SETTINGS = {
    "the old bridge": True,
    "the village square": True,
    "the forest edge": True,
    "the hilltop mill": True,
}
NAMES = ["Luna", "Pip", "Mara", "Toby", "Nia", "Bo", "Suri", "Finn"]
MESSAGES = [
    "the river is rising",
    "come home before dark",
    "the harvest is ready",
    "share the warm bread",
]


SCENARIOS = [
    Scenario(
        "bird-song",
        "found a thrush who knew the message only as a song",
        "The bird understood Luna's words but could not carry them across the noisy valley.",
        "shouting the message made the wind scatter every word",
        "the thrush repeated the message as three clear notes",
        "translate the words into a rhythm and pass the rhythm from friend to friend",
        ("tapped the first beat on a hollow rail", "listened for the last beat and answered across the bridge"),
        "The rhythm crossed the valley, and the far villagers began preparing at once.",
        "teamwork can turn one small voice into a message that travels far",
        "the thrush sang above the bridge while many villagers moved together below",
    ),
    Scenario(
        "painted-stones",
        "gathered smooth stones and painted a sign for travelers",
        "Their pictures meant one thing to Luna and another to Pip.",
        "adding more pictures made the sign harder to understand",
        "a simple sun, path, and bowl appeared in both their drawings",
        "translate the message into three shared pictures and place them in order",
        ("washed the stones and painted the sun and path", "painted the bowl and tested the order with a traveler"),
        "The traveler read the stones correctly and carried the warning onward.",
        "a shared meaning is stronger than a clever sign understood by only one person",
        "three bright stones marked the way beside the road, clear to every passerby",
    ),
    Scenario(
        "echo-cave",
        "entered a cave where every sound returned changed",
        "The echo turned 'come home' into a jumble that sent a goat toward the cliffs.",
        "repeating the same words louder only made the jumble louder",
        "short sounds returned clearly when they were separated by a pause",
        "translate the message into short calls and let each helper wait before answering",
        ("called the first short sound and watched the goat", "counted the pause and gave the next call"),
        "The goat followed the clear calls back to the safe meadow.",
        "patience and teamwork can transform confusion into a useful path",
        "the cave kept one gentle echo while the goat nibbled safely in the meadow",
    ),
    Scenario(
        "silent-dance",
        "met a fox who spoke with paws and tail instead of words",
        "Luna's spoken directions meant nothing to the fox beside the rushing stream.",
        "pointing in many directions made the fox spin in circles",
        "the fox touched its left paw whenever it wanted the safe path",
        "translate the warning into three gestures and perform them together",
        ("learned the fox's sign for stop and safe", "matched each gesture with a clear place to move"),
        "The fox understood the new dance and led them around the broken bank.",
        "listening to another creature can reveal a way words cannot",
        "fox, children, and birds crossed the safe stones in one quiet procession",
    ),
    Scenario(
        "mill-bells",
        "noticed that the mill bells could warn the village",
        "A loose bell rang at random, so the villagers could not tell warning from welcome.",
        "pulling the rope harder made every bell answer at once",
        "the smallest bell had three steady notes when the rope was held still",
        "translate the danger into a three-note pattern and work the rope together",
        ("held the rope steady beneath the small bell", "counted three notes and signaled when to stop"),
        "The pattern rang clearly, and the village left the low fields in time.",
        "a careful pattern can transform noise into knowledge",
        "the bells rested in the quiet tower after every family reached high ground",
    ),
    Scenario(
        "woven-map",
        "found a traveling weaver who used colored threads as words",
        "The road map had slipped apart, leaving the safest way hidden.",
        "pulling the threads from opposite ends tore the map farther",
        "matching colors joined whenever two hands held them gently",
        "translate the road into a woven pattern and mend it side by side",
        ("sorted the red and gold threads by the stream", "joined the blue crossings beside the old oak"),
        "The finished map showed a safe way around the flooded road.",
        "transformation begins when patient hands repair what haste damages",
        "the woven map hung from the oak, its bright road guiding every traveler",
    ),
    Scenario(
        "beetle-lanterns",
        "asked glowing beetles to guide a lost child",
        "The beetles understood light but not the pointing paws of the worried child.",
        "waving wildly made the beetles scatter into the dark",
        "two slow lantern flashes made them gather in a line",
        "translate the child's need into flashes and follow the beetles together",
        ("shielded the lantern to make two steady flashes", "watched the child and followed the glowing line"),
        "The beetles led everyone to the warm village gate.",
        "when helpers use the same language, fear can change into direction",
        "a trail of beetle-lights curled home like a necklace through the grass",
    ),
    Scenario(
        "rain-drum",
        "heard a cloud giant tapping a warning on the roof",
        "The giant's deep rhythm sounded like thunder to the villagers.",
        "answering with random knocks made the roof shake harder",
        "the rhythm repeated after every four quiet heartbeats",
        "translate the taps into a count and answer only after listening",
        ("counted the quiet heartbeats beside the door", "answered with four gentle taps on a clay drum"),
        "The cloud giant understood and moved the storm beyond the valley.",
        "listening before answering can transform a frightening sound into a conversation",
        "rain softened to silver threads while the clay drum gleamed by the door",
    ),
]


OPENINGS = [
    "At dawn, {a} and {b} stood in {setting} with a message between them.",
    "In {setting}, {a} heard a problem that words alone could not solve.",
    "A little message waited beside the path in {setting}.",
    "The village was waking when {a} and {b} met in {setting}.",
    "Near {setting}, a traveler asked for help carrying one important thought.",
]

REACTIONS = [
    "'The message is true, but nobody understands it,' {a} said.",
    "{b} tilted their head. 'Perhaps we need a different way.'",
    "'Louder is not clearer,' {b} warned.",
    "The two friends looked at each other instead of blaming the messenger.",
    "'Let us listen before we change anything,' {a} said.",
]

MORALS = [
    "A message becomes useful when people build its meaning together.",
    "Teamwork is a way of making one person's small strength part of a larger strength.",
    "Transformation does not erase an idea; it gives the idea a form others can receive.",
    "The wisest way forward begins with listening.",
]


def generate_world(p: StoryParams) -> World:
    if p.first_name == p.second_name:
        raise StoryError("The two helpers must have different names.")
    if p.message not in MESSAGES:
        raise StoryError("The message must come from the registered village messages.")

    world = World(p.setting)
    first = world.add(Entity("first_helper", "character", p.first_name))
    second = world.add(Entity("second_helper", "character", p.second_name))
    message = world.add(Entity("message", "idea", p.message))
    seed = abs(p.seed or 0)
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // 8) % len(OPENINGS)]
    reaction = REACTIONS[(seed // 64) % len(REACTIONS)]
    moral = MORALS[(seed // 512) % len(MORALS)]

    world.say(opening.format(a=first.label, b=second.label, setting=p.setting))
    world.say(f"{first.label} carried the thought that {message.label}.")
    world.say(f"Together, the friends {scenario.premise}.")
    world.para()
    world.say(scenario.obstacle)
    world.say(reaction.format(a=first.label, b=second.label))
    world.say(f"At first, {first.label} tried alone, but {scenario.failed}.")
    world.say(f"Then {second.label} noticed a clue: {scenario.clue}.")
    world.para()
    world.say(f"The clue changed their plan. They would {scenario.plan}.")
    world.say(f"{first.label} {scenario.jobs[0]}, while {second.label} {scenario.jobs[1]}.")
    world.say(f"They did not merely repeat the message; they transformed it so others could receive it. {scenario.result}")
    world.para()
    world.say(f"{first.label} asked, 'Did our new way carry the same meaning?'")
    world.say(f"{second.label} answered, 'Yes. We changed its shape, not its heart.'")
    world.say(f"They learned that {scenario.lesson}.")
    world.say(f"{moral} At the end, {scenario.ending}")

    first.memes.update(teamwork=1.0, understanding=1.0, transformed=1.0)
    second.memes.update(teamwork=1.0, understanding=1.0, transformed=1.0)
    message.meters.update(carried=1.0, translated=1.0)
    world.facts.update(
        first=first.label,
        second=second.label,
        message=message.label,
        scenario=scenario.key,
        obstacle=scenario.obstacle,
        failed=scenario.failed,
        clue=scenario.clue,
        plan=scenario.plan,
        first_job=scenario.jobs[0],
        second_job=scenario.jobs[1],
        result=scenario.result,
        lesson=scenario.lesson,
        moral=moral,
        ending=scenario.ending,
        translated=True,
        teamwork=True,
        transformation=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What problem did {f['first']} and {f['second']} face?",
            answer=f"They faced this problem: {f['obstacle']} Their first attempt failed because {f['failed']}.",
        ),
        QAItem(
            question="What clue showed them a better way?",
            answer=f"They noticed that {f['clue']} This clue helped them choose a shared method.",
        ),
        QAItem(
            question="How did the helpers divide the work?",
            answer=f"{f['first']} {f['first_job']}, while {f['second']} {f['second_job']}. Their separate jobs worked together.",
        ),
        QAItem(
            question="How did they translate the message?",
            answer=f"They translated it by deciding to {f['plan']} The transformation kept the message's meaning while changing its form.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The teamwork succeeded: {f['result']} The ending image was that {f['ending']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to translate something?",
            answer="To translate something means to carry its meaning from one language, form, or system into another.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people listen, divide useful jobs, and combine their efforts toward one goal.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change in shape, condition, or form.",
        ),
        QAItem(
            question="Why can listening help solve a problem?",
            answer="Listening can reveal patterns and needs that are hidden when someone rushes to speak or act.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fable about {f['first']} and {f['second']} finding a way to translate the message that {f['message']}.",
        f"Tell a teamwork story in {world.setting} where the clue is that {f['clue']}.",
        "Create a child-friendly fable showing transformation without losing the heart of an idea.",
    ]


ASP_RULES = r"""
helper_pair(A,B) :- helper(A), helper(B), A < B.
teamwork(A,B) :- helper_pair(A,B), contributes(A), contributes(B).
translated(M) :- message(M), method(M), teamwork(_, _).
transformation(M) :- translated(M), changed_form(M), preserved_meaning(M).
successful_way(M) :- transformation(M), carried(M).
#show teamwork/2.
#show translated/1.
#show transformation/1.
#show successful_way/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("helper", "luna"),
        asp.fact("helper", "pip"),
        asp.fact("contributes", "luna"),
        asp.fact("contributes", "pip"),
        asp.fact("message", "river_rising"),
        asp.fact("method", "rhythm"),
        asp.fact("changed_form", "river_rising"),
        asp.fact("preserved_meaning", "river_rising"),
        asp.fact("carried", "river_rising"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show successful_way/1."))
    found = asp.atoms(symbols, "successful_way")
    print("OK: ASP found a translated message carried by teamwork." if found else "MISMATCH: ASP found no successful way.")
    return 0 if found else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--first-name")
    parser.add_argument("--second-name")
    parser.add_argument("--message", choices=MESSAGES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    first = args.first_name or rng.choice(NAMES)
    second = args.second_name or rng.choice([name for name in NAMES if name != first])
    if first == second:
        raise StoryError("The two helpers must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        first_name=first,
        second_name=second,
        message=args.message or rng.choice(MESSAGES),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the old bridge", "Luna", "Pip", "the river is rising", 7),
    StoryParams("the village square", "Mara", "Toby", "come home before dark", 91),
    StoryParams("the forest edge", "Nia", "Bo", "the harvest is ready", 203),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        facts = sample.world.facts
        print(
            "\n--- world model state ---\n"
            f"scenario={facts['scenario']} translated={facts['translated']} "
            f"teamwork={facts['teamwork']} transformation={facts['transformation']}"
        )
    if qa:
        for index, item in enumerate(sample.story_qa, 1):
            print(f"Q{index}: {item.question}\nA{index}: {item.answer}")
        for index, item in enumerate(sample.world_qa, 1):
            print(f"W{index}: {item.question}\nA{index}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show teamwork/2. #show translated/1. #show transformation/1. #show successful_way/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show teamwork/2. #show translated/1. #show transformation/1."))
        for symbol in symbols:
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(params) for params in CURATED] if args.all else []
    if not args.all:
        if args.n < 1:
            raise StoryError("The number of stories must be at least one.")
        for index in range(args.n):
            params = resolve_params(args, random.Random(base + index))
            params.seed = base + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
