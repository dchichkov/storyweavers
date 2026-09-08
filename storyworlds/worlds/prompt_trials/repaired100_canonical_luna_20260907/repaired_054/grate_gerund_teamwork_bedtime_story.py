#!/usr/bin/env python3
"""A gentle bedtime StoryWorld about grate-gerund and teamwork."""

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    setting: str = "the moonlit bedroom"
    first_name: str = "Luna"
    second_name: str = "Milo"
    object_name: str = "the silver night-light"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    failed: str
    clue: str
    plan: str
    jobs: tuple[str, str]
    result: str
    lesson: str
    ending: str


SETTINGS = {
    "the moonlit bedroom": True,
    "the quiet nursery": True,
    "the little attic room": True,
    "the starlit tent": False,
}

NAMES = ["Luna", "Milo", "Nora", "Theo", "Iris", "Sam", "Ada", "Finn"]
OBJECTS = [
    ("the silver night-light", "light"),
    ("the blue music box", "music box"),
    ("the sleepy star lamp", "lamp"),
    ("the little moon blanket", "blanket"),
]

SCENARIOS = [
    Scenario(
        "shadow-grate",
        "made a tiny grate-shaped window from wooden blocks for moonbeams",
        "The night-light cast a crooked shadow, and neither child could see the path to the bed.",
        "moving the blocks alone made the shadow taller and darker",
        "the grate became straight only when two hands held its opposite corners",
        "hold the corners together, place the light low, and guide the moonbeam toward the bed",
        ("held the left corner steady", "turned the right corner until the lines matched"),
        "A soft square of light crossed the floor, making a safe path for sleepy feet.",
        "teamwork means joining different jobs to make one gentle result",
        "the little grate-shadow rested on the rug like a silver window while everyone grew calm",
    ),
    Scenario(
        "blanket-fort",
        "built a small blanket fort beside the bed",
        "One corner sagged whenever either child tried to tuck in alone.",
        "pulling harder only made the blanket slip from its chair",
        "the cloth stayed smooth when one child lifted and the other tucked",
        "lift the blanket together, then fasten its corner with a soft ribbon",
        ("raised the blanket above the pillow", "tied the ribbon around the steady chair"),
        "The fort became a warm roof where both children could whisper good-night.",
        "a shared task can become easy when each person takes a useful part",
        "the blanket fort glowed softly beneath the lamp, with two quiet heads inside",
    ),
    Scenario(
        "star-map",
        "arranged paper stars into a map for a bedtime voyage",
        "The stars scattered when the rug was bumped, and the map lost its way.",
        "gathering every star alone made the other stars slide away",
        "the map stayed still when one pair of hands held the paper flat",
        "hold the map, sort the stars, and place the brightest one at the end",
        ("pressed the corners flat against the rug", "sorted the stars by size and placed the guide star"),
        "The finished map led from the pillow to a bright paper moon.",
        "teamwork lets one person protect the work while another completes it",
        "the paper moon shone at the end of the map as sleepy eyes followed its trail",
    ),
    Scenario(
        "whisper-bell",
        "hung a tiny bell beside the bedtime story chair",
        "The bell rang too soon whenever one child reached for the book.",
        "trying to silence it with one hand made the book wobble",
        "the bell stayed quiet when one child held the cord and the other opened the book",
        "hold the cord, open the book slowly, and ring the bell only at the final page",
        ("kept the cord still beside the chair", "turned each page with careful fingers"),
        "The bell gave one clear chime after the last page, just as bedtime arrived.",
        "quiet teamwork can protect a peaceful ending",
        "the bell rested silent while the storybook closed beneath a moon-shaped bookmark",
    ),
    Scenario(
        "pillow-bridge",
        "made a bridge of pillows from the reading rug to the bed",
        "A gap opened in the middle, leaving the favorite bear on the far side.",
        "pushing every pillow at once made the bridge bend",
        "the bridge grew firm when the pillows were passed one at a time",
        "pass, place, and press each pillow until the path reaches the bed",
        ("passed the pillows from the rug", "placed and pressed them into a steady path"),
        "The bear crossed safely, and the children carried the last pillow together.",
        "teamwork turns small careful actions into a strong path",
        "the teddy bear slept at the head of the bed beside the completed pillow bridge",
    ),
    Scenario(
        "rainy-window",
        "placed paper clouds beneath the rainy window",
        "A draft lifted the clouds and scattered their silver raindrops.",
        "chasing the loose papers made more clouds fly away",
        "the clouds stayed put beneath a row of smooth stones",
        "hold the papers low, gather the stones, and make a calm sky",
        ("caught the clouds before they reached the door", "lined the stones along their edges"),
        "The paper sky stayed still while rain whispered outside.",
        "working together can make a calm place during a noisy moment",
        "the silver raindrops rested beneath the paper clouds as the real rain softened",
    ),
    Scenario(
        "sleepy-clock",
        "set a wooden clock to mark the hour for dreams",
        "The hands pointed in different directions after the clock was bumped.",
        "turning the hands without holding the clock made them wobble again",
        "the hands met at midnight when one child held the clock face",
        "steady the clock, turn the hands slowly, and check the moon mark",
        ("held the clock firmly on the table", "turned the hands toward the moon mark"),
        "The clock showed dreamtime, and both children knew it was time to rest.",
        "teamwork helps careful choices stay steady",
        "the wooden clock ticked softly beside the bed, pointing to the moon",
    ),
    Scenario(
        "lost-lullaby",
        "kept a lullaby card beside the pillow",
        "A breeze slid the card beneath the bed before the song began.",
        "reaching from one side pushed the card farther into the dark",
        "the card stopped when a slipper blocked its corner",
        "shine the lamp, hold the slipper still, and pull the card out gently",
        ("held the lamp close to the floor", "blocked the slipper and pulled the card by its corner"),
        "They found the lullaby and sang it softly without waking the house.",
        "teamwork means helping another person see and reach what is needed",
        "the lullaby card lay on the pillow while its final note faded into sleep",
    ),
    Scenario(
        "dream-door",
        "painted a small cardboard door for an imaginary dream garden",
        "The door would not stand because its paper hinges folded inward.",
        "propping it with one toy made it lean toward the floor",
        "the door balanced when two blocks supported opposite sides",
        "place the blocks together, straighten the hinges, and open the dream door",
        ("held one block beneath the left side", "straightened the hinge and placed the second block"),
        "The door stood open to a garden of paper flowers.",
        "two kinds of help can support one hopeful idea",
        "the cardboard dream door stood beneath the stars, open to a garden no one had to leave",
    ),
    Scenario(
        "quiet-train",
        "lined up wooden cars for a silent bedtime train",
        "The cars bumped and woke the doll tucked beside the track.",
        "pulling the train faster made the bumps louder",
        "the cars moved smoothly when one child guided the front and one slowed the back",
        "guide the train slowly and protect the sleeping doll",
        ("guided the front car around the bend", "held the last car and watched the doll"),
        "The train passed the doll in a whisper and reached its station.",
        "teamwork can care for others while finishing a shared plan",
        "the wooden train rested at its station as the doll slept undisturbed",
    ),
    Scenario(
        "moon-grate",
        "balanced a small paper grate over a bowl to catch moon-shaped stars",
        "The grate tilted, and the paper stars slid into one bright pile.",
        "fixing one corner at a time made the opposite corner tip",
        "the grate became level when both sides were lifted together",
        "lift both sides, settle the grate, and scatter the stars gently",
        ("lifted the near side at the same moment", "settled the far side and scattered the stars"),
        "The stars rested in separate spaces like tiny windows of light.",
        "a difficult balance may need two people moving together",
        "the moon-grate held its stars while pale light filled every little square",
    ),
    Scenario(
        "goodnight-basket",
        "made a basket for bedtime treasures",
        "The handle bent when both children tried to carry it from opposite ends.",
        "pulling apart made the handle creak",
        "the handle felt strong when they carried it at the same height",
        "walk together, lift evenly, and place the treasures beside the bed",
        ("lifted the left side at the agreed height", "matched the lift and watched the path"),
        "The basket reached the bed without a single treasure falling out.",
        "teamwork depends on listening and moving at the same pace",
        "the basket sat beside the bed, full of treasures and ready for morning",
    ),
]


OPENINGS = [
    "When the moon climbed above {setting}, {a} and {b} were still awake.",
    "In {setting}, a small bedtime task waited beneath the quiet stars.",
    "{a} and {b} whispered together in {setting} while the house grew still.",
    "The moonlight made a silver patch on the floor of {setting}.",
    "Just before sleep, {a} and {b} found one last gentle thing to do.",
    "A tiny problem stirred beside {object_name} in {setting}.",
]

REACTIONS = [
    "'We should not hurry,' {a} whispered.",
    "{b} looked at the crooked work. 'It needs both of us.'",
    "'I can help you,' said {a}, keeping their voice soft.",
    "{b} took a slow breath. 'Let us listen to the quiet clue.'",
    "For a moment, both children reached at once, then they lowered their hands.",
    "'Teamwork,' {a} said, 'means we do not have to do the same job.'",
]

TURNS = [
    "That was the turn in their bedtime plan: they stopped pulling and started listening.",
    "The clue changed their question from 'Who can fix it?' to 'How can we help together?'",
    "They made room for two jobs instead of one hurried attempt.",
    "The quiet room seemed to answer when they tested the clue side by side.",
    "Their worry softened as soon as each child had a clear part to do.",
]

GERUNDS = [
    "By holding, turning, and listening, they made their teamwork gentle.",
    "Their careful helping became a little grate-gerund: holding the pieces together while the peaceful work continued.",
    "Grate-gerund meant doing the small useful action that let another person succeed.",
    "They remembered that helping, steadying, and sharing could turn a hard moment soft.",
]


def generate_world(params: StoryParams) -> World:
    if params.first_name == params.second_name:
        raise StoryError("The two bedtime helpers must have different names.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown bedtime setting: {params.setting}")
    if params.object_name not in {item[0] for item in OBJECTS}:
        raise StoryError(f"Unknown bedtime object: {params.object_name}")

    world = World(params.setting)
    first = world.add(Entity("first_helper", "character", params.first_name))
    second = world.add(Entity("second_helper", "character", params.second_name))
    object_entity = world.add(Entity("bedtime_object", "thing", params.object_name))

    value = abs(params.seed or 0)
    scene = SCENARIOS[value % len(SCENARIOS)]
    opening = OPENINGS[(value // 13) % len(OPENINGS)]
    reaction = REACTIONS[(value // 29) % len(REACTIONS)]
    turn = TURNS[(value // 47) % len(TURNS)]
    gerund = GERUNDS[(value // 71) % len(GERUNDS)]

    world.say(
        opening.format(
            setting=params.setting,
            a=first.label,
            b=second.label,
            object_name=object_entity.label,
        )
    )
    world.say(
        f"{first.label} and {second.label} were caring for {object_entity.label}; "
        f"together, they {scene.premise}."
    )
    world.para()
    world.say(scene.trouble)
    world.say(reaction.format(a=first.label, b=second.label))
    world.say(f"At first, {first.label} tried alone, but {scene.failed}.")
    world.say(f"Then {second.label} noticed a clue: {scene.clue}.")
    world.para()
    world.say(turn)
    world.say(f"Their plan was to {scene.plan}.")
    world.say(f"{first.label} {scene.jobs[0]}, while {second.label} {scene.jobs[1]}.")
    world.say(gerund)
    world.say(f"Together, they finished the work. {scene.result}")
    world.para()
    world.say(f"{first.label} whispered, 'We did it together.'")
    world.say(
        f"{second.label} smiled and answered, 'Yes. {scene.lesson.capitalize()}.'"
    )
    world.say(f"The room grew peaceful. {scene.ending}.")

    first.memes.update(teamwork=1.0, calm=1.0)
    second.memes.update(teamwork=1.0, calm=1.0)
    object_entity.meters.update(safe=1.0, complete=1.0)
    world.facts.update(
        first=first.label,
        second=second.label,
        object=object_entity.label,
        scenario=scene.key,
        trouble=scene.trouble,
        failed=scene.failed,
        clue=scene.clue,
        plan=scene.plan,
        first_job=scene.jobs[0],
        second_job=scene.jobs[1],
        result=scene.result,
        lesson=scene.lesson,
        ending=scene.ending,
        teamwork=True,
        complete=True,
        gerund=gerund,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    trouble = str(facts["trouble"])
    return [
        QAItem(
            question=f"What bedtime problem did {facts['first']} and {facts['second']} face?",
            answer=(
                f"They faced this problem: {trouble} "
                "Their bedtime work could not continue until they solved it."
            ),
        ),
        QAItem(
            question="What clue helped the children change their plan?",
            answer=(
                f"They noticed that {facts['clue']}. "
                "The clue showed them that careful teamwork would work better than rushing."
            ),
        ),
        QAItem(
            question="How did the children share the work?",
            answer=(
                f"{facts['first']} {facts['first_job']}, while "
                f"{facts['second']} {facts['second_job']}. "
                "Their two jobs supported the same peaceful goal."
            ),
        ),
        QAItem(
            question="What did teamwork change in the story?",
            answer=(
                f"Teamwork changed the problem into a finished bedtime task. "
                f"{facts['result']}"
            ),
        ),
        QAItem(
            question="How did the bedtime story end?",
            answer=(
                f"They learned that {facts['lesson']}. "
                f"The ending image was this: {facts['ending']}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer=(
                "Teamwork is cooperating toward one goal by listening, sharing jobs, "
                "and helping one another."
            ),
        ),
        QAItem(
            question="What is a grate?",
            answer=(
                "A grate is a frame or set of crossing bars with open spaces between them. "
                "It can let light or air pass through."
            ),
        ),
        QAItem(
            question="What is a gerund?",
            answer=(
                "A gerund is a verb form ending in -ing that can name an activity, "
                "such as helping, holding, or listening."
            ),
        ),
        QAItem(
            question="Why is bedtime teamwork useful?",
            answer=(
                "Bedtime teamwork is useful because quiet shared actions can solve a problem "
                "without making the room noisy or upsetting."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a gentle bedtime story about {facts['first']} and {facts['second']} using teamwork.",
        (
            f"Tell a child-friendly story in {world.setting} where {facts['first']} "
            f"and {facts['second']} solve a problem involving {facts['object']}."
        ),
        (
            "Create a bedtime story featuring a grate-gerund idea: a small "
            "helping action in -ing form that allows teamwork to succeed."
        ),
    ]


ASP_RULES = r"""
helper(X) :- child(X).
teamwork(X,Y) :- helper(X), helper(Y), X != Y, helps(X,Y).
shared_goal(G) :- goal(G), works_on(X,G), works_on(Y,G), X != Y.
peaceful_finish(G) :- shared_goal(G), completed(G), quiet(G).
#show teamwork/2.
#show shared_goal/1.
#show peaceful_finish/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("child", "luna"),
        asp.fact("child", "milo"),
        asp.fact("helps", "luna", "milo"),
        asp.fact("helps", "milo", "luna"),
        asp.fact("goal", "bedtime_task"),
        asp.fact("works_on", "luna", "bedtime_task"),
        asp.fact("works_on", "milo", "bedtime_task"),
        asp.fact("completed", "bedtime_task"),
        asp.fact("quiet", "bedtime_task"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(
        asp_program("#show teamwork/2. #show shared_goal/1. #show peaceful_finish/1.")
    )
    teamwork = asp.atoms(symbols, "teamwork")
    goals = asp.atoms(symbols, "shared_goal")
    finishes = asp.atoms(symbols, "peaceful_finish")
    sample = generate(StoryParams(seed=17))
    ok = bool(teamwork and goals and finishes and "teamwork" in sample.story.lower())
    if ok:
        print("OK: ASP and Python both represent peaceful bedtime teamwork.")
        return 0
    print("MISMATCH: bedtime teamwork parity check failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--first-name")
    parser.add_argument("--second-name")
    parser.add_argument("--object", dest="object_name", choices=[item[0] for item in OBJECTS])
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
    second_choices = [name for name in NAMES if name != first]
    second = args.second_name or rng.choice(second_choices)
    if first == second:
        raise StoryError("The two bedtime helpers must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        first_name=first,
        second_name=second,
        object_name=args.object_name or rng.choice([item[0] for item in OBJECTS]),
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
    StoryParams("the moonlit bedroom", "Luna", "Milo", "the silver night-light", 3),
    StoryParams("the quiet nursery", "Nora", "Theo", "the blue music box", 29),
    StoryParams("the starlit tent", "Iris", "Finn", "the little moon blanket", 71),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        facts = sample.world.facts
        print(
            "\n--- world model state ---\n"
            f"scenario={facts['scenario']} teamwork={facts['teamwork']} "
            f"complete={facts['complete']}"
        )
    if qa:
        for index, item in enumerate(sample.story_qa, 1):
            print(f"Q{index}: {item.question}\nA{index}: {item.answer}")
        for index, item in enumerate(sample.world_qa, 1):
            print(f"W{index}: {item.question}\nA{index}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show teamwork/2. #show shared_goal/1. #show peaceful_finish/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show teamwork/2. #show shared_goal/1. #show peaceful_finish/1."))
        print(json.dumps({
            "teamwork": [list(item) for item in asp.atoms(symbols, "teamwork")],
            "shared_goal": [list(item) for item in asp.atoms(symbols, "shared_goal")],
            "peaceful_finish": [list(item) for item in asp.atoms(symbols, "peaceful_finish")],
        }, indent=2))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
        emit(
            sample,
            args.trace,
            args.qa,
            f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
