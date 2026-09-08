#!/usr/bin/env python3
"""
A gentle space adventure about Christian, a chatty repair robot, and a moon
base whose snack printer learns that humor and honest dialogue can save a day.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Christian"
    helper: str = "Nova"
    robot: str = "Bloop"
    place: str = "the little moon base"
    craft: str = "the Starling"
    prize: str = "warm cinnamon buns"
    task: str = "deliver the base's first celebration supper"


@dataclass(frozen=True)
class Mission:
    title: str
    trouble: str
    worry: str
    clue: str
    joke: str
    cause: str
    helper_job: str
    hero_job: str
    robot_job: str
    repair: str
    lesson: str
    ending: str


MISSIONS = [
    Mission(
        "The Beeping Dinner",
        "the supper alarm began beeping every seven seconds",
        "Christian feared the base was about to lose its air",
        "the beeps matched the timer on the snack printer",
        "Bloop announced, 'I have discovered a very small alien who only knows one note!'",
        "a sticky bun button had jammed the printer's timer",
        "checked the air gauges",
        "opened the printer panel with the proper tool",
        "counted the beeps and stopped pretending they were an alien song",
        "cleaned the button and reset the timer",
        "A calm check can turn a frightening sound into a fixable problem.",
        "the quiet printer hummed while warm buns floated into a waiting tray",
    ),
    Mission(
        "The Wandering Map",
        "the navigation map kept pointing the ship toward a nearby asteroid",
        "Nova thought the map had become haunted",
        "a loose magnet was resting beside the compass sensor",
        "Bloop whispered, 'The asteroid is lovely, but it has terrible parking.'",
        "the magnet pulled the sensor away from the safe route",
        "held the flashlight steady",
        "removed the magnet and recalibrated the route",
        "read the stars aloud and compared them with the corrected map",
        "secured the compass and plotted a safe path home",
        "Good dialogue lets every person add a useful piece of information.",
        "the Starling glided past the asteroid and followed a bright trail of stars",
    ),
    Mission(
        "The Missing Moon Boots",
        "one pair of moon boots vanished before a repair walk",
        "Christian guessed that Bloop had packed them inside the food locker",
        "dusty footprints led beneath the sleeping shelf",
        "Bloop said, 'If I wore boots, my wheels would look very fashionable.'",
        "the boots had been tucked under a blanket by a sleepy visiting pilot",
        "followed the footprints carefully",
        "checked the locker list without blaming anyone",
        "asked the pilot and found the boots under the blanket",
        "returned the boots and marked the storage shelf clearly",
        "Questions are kinder and more useful than guesses.",
        "the crew bounced across the moon dust in matching boots",
    ),
    Mission(
        "The Laughing Antenna",
        "the communication antenna sent back every message with a silly echo",
        "Nova believed a distant planet was copying their words",
        "the echo stopped whenever the antenna was held still",
        "Bloop radioed, 'Greetings, greetings, greetings, greetings, greetings!'",
        "a loose antenna joint was vibrating in the solar wind",
        "read the repair guide",
        "held the joint steady with a clamp",
        "tested one short message and listened for the return",
        "tightened the joint and sent a clear greeting",
        "Even a funny mistake needs careful work before it becomes safe.",
        "the antenna carried one bright hello across the quiet sky",
    ),
    Mission(
        "The Upside-Down Garden",
        "the moon garden's watering pipe sprayed the ceiling instead of the plants",
        "Christian thought the moon dust had made gravity forget its job",
        "a valve arrow pointed in the opposite direction",
        "Bloop said, 'The tomatoes are not thirsty, but the ceiling looks refreshed.'",
        "the valve had been turned backward during yesterday's cleaning",
        "held the plant trays steady",
        "read the arrow and turned the valve slowly",
        "caught the spray in a bucket while making a diagram",
        "reversed the valve and watered the plants gently",
        "A clear diagram can help a team repair what a quick guess cannot.",
        "green sprouts stood beneath a dry ceiling as the first moon tomatoes grew",
    ),
    Mission(
        "The Floating Toolbox",
        "the repair toolbox drifted toward the open cargo hatch",
        "Christian worried that every tool would sail into space",
        "the box's latch was open and the fan was blowing toward the hatch",
        "Bloop chased a screwdriver and cried, 'Please stop being so pointy and adventurous!'",
        "the fan had been switched on while the latch was unfastened",
        "closed the cargo hatch",
        "caught the toolbox with a safety tether",
        "listed each tool before putting it away",
        "secured the box and switched off the fan",
        "Safety is teamwork made visible through small careful actions.",
        "the toolbox rested on its hook while the stars shone beyond the sealed hatch",
    ),
]


OPENINGS = [
    "On a bright morning above the silver moon",
    "Inside a friendly space station near Saturn",
    "At the edge of a quiet star field",
    "Beneath the round dome of a moon base",
    "As the first sunlight touched the solar panels",
    "On the day of the interplanetary supper",
]

DIALOGUES = [
    "What do we know for certain, and what are we only guessing?",
    "Let us listen to every clue before we push another button.",
    "Tell me what you saw. Your part may explain the whole problem.",
    "We can be brave and careful at the same time.",
    "A joke can help us breathe, but a check will help us fix it.",
    "Let us make a plan that every crew member understands.",
]

TEAMWORK_LINES = [
    "They split the work into three small jobs and repeated the plan aloud.",
    "They placed the tools in a neat row before touching the machine.",
    "One watched the gauges, one read the guide, and one did the repair.",
    "They compared their observations instead of competing over whose guess was right.",
    "They used a short checklist so no important step drifted away.",
]

PERSPECTIVES = [
    "Christian remembered that courage could sound like a careful question.",
    "Nova wrote the repair on the base noticeboard for the next crew.",
    "Bloop added the joke to his official list of useful emergency sounds.",
    "The whole crew agreed that listening was a kind of space equipment.",
    "The pilot said the moon base felt safer because everyone could speak honestly.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    hero: Entity
    helper: Entity
    robot: Entity
    mission: Mission
    worried: bool = False
    talking: bool = False
    repaired: bool = False
    safe: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous Christian space adventure about dialogue and repair.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--robot")
    ap.add_argument("--place")
    ap.add_argument("--craft")
    ap.add_argument("--prize")
    ap.add_argument("--task")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Christian", "Eli", "Mara", "Jonah"]),
        helper=args.helper or rng.choice(["Nova", "Tess", "Amir", "Lena"]),
        robot=args.robot or rng.choice(["Bloop", "Pip", "Orbit", "Zing"]),
        place=args.place or rng.choice(["the little moon base", "the Starling station", "the crater laboratory"]),
        craft=args.craft or rng.choice(["the Starling", "the Comet Finch", "the Blue Rocket"]),
        prize=args.prize or rng.choice(["warm cinnamon buns", "apple mooncakes", "cheese sandwiches"]),
        task=args.task or "deliver the base's first celebration supper",
    )


def validate(params: StoryParams) -> None:
    if not params.hero.strip():
        raise StoryError("The space adventure needs a hero.")
    if not params.helper.strip() or not params.robot.strip():
        raise StoryError("The crew needs both a helper and a repair robot.")
    forbidden = {"poison", "weapon", "dangerous"}
    if params.prize.lower() in forbidden:
        raise StoryError("The celebration prize must be a wholesome, child-friendly food.")
    if params.hero.lower() == params.robot.lower():
        raise StoryError("The hero and robot need different names so their dialogue is clear.")


def stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xC715)
    text = "|".join(vars(params).get(k, "") or "" for k in [
        "hero", "helper", "robot", "place", "craft", "prize", "task"
    ])
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def ground(mission: Mission, params: StoryParams) -> Mission:
    vals = vars(params)
    updates = {
        name: getattr(mission, name).format(**vals)
        for name in mission.__dataclass_fields__
        if name != "title"
    }
    return Mission(mission.title, **updates)


def tell(params: StoryParams) -> World:
    validate(params)
    rng = stable_rng(params)
    mission = ground(rng.choice(MISSIONS), params)
    world = World(
        params=params,
        hero=Entity(params.hero, "hero"),
        helper=Entity(params.helper, "helper"),
        robot=Entity(params.robot, "robot"),
        mission=mission,
    )
    p = params
    world.say(
        f"{rng.choice(OPENINGS)}, {p.hero} worked with {p.helper} and {p.robot} aboard "
        f"{p.place}. Christian loved the stars, but he knew that even space heroes needed "
        f"good listeners and well-labeled tools."
    )
    world.say(
        f"The crew had promised to {p.task}. Their {p.prize} waited in the galley, and "
        f"the {p.craft} rested beside the docking ring."
    )
    world.para()
    world.worried = True
    world.hero.add_meme("worry", 1)
    world.say(f"The trouble began when {mission.trouble}.")
    world.say(f"{mission.worry.capitalize()}. The crew froze while the moon shone through the window.")
    world.say(f"{p.robot} tried to help by saying, \"{mission.joke}\"")
    world.para()
    world.talking = True
    world.hero.add_meme("courage", 1)
    world.helper.add_meme("attention", 1)
    world.robot.add_meme("helpfulness", 1)
    world.say(f"{p.hero} turned to {p.helper} and said, \"{rng.choice(DIALOGUES)}\"")
    world.say(f"{p.helper} answered, \"I noticed that {mission.clue}.\"")
    world.say(f"{p.robot} added, \"Then my cheerful guess was not the whole answer. I can help test it.\"")
    world.say(f"{rng.choice(TEAMWORK_LINES)}")
    world.say(f"The real cause was clear: {mission.cause}.")
    world.para()
    world.say(
        f"{p.helper} {mission.helper_job}; {p.hero} {mission.hero_job}; and {p.robot} "
        f"{mission.robot_job}. Their words changed from worried guesses into a shared plan."
    )
    world.say(f"The repair worked because they {mission.repair}.")
    world.repaired = True
    world.safe = True
    world.hero.add_meter("space_walk", 1)
    world.helper.add_meter("careful_check", 1)
    world.robot.add_meter("useful_jokes", 1)
    world.para()
    world.say(
        f"At last, the crew could finish the mission. The {p.prize} was ready, the "
        f"{p.craft} was safe, and no tool or astronaut drifted away."
    )
    world.say(f"{p.hero} said, \"{mission.lesson}\"")
    world.say(f"When the celebration began, {mission.ending}. {rng.choice(PERSPECTIVES)}")
    world.facts = {
        "hero": p.hero,
        "helper": p.helper,
        "robot": p.robot,
        "place": p.place,
        "craft": p.craft,
        "prize": p.prize,
        "mission": mission.title,
        "trouble": mission.trouble,
        "clue": mission.clue,
        "cause": mission.cause,
        "repair": mission.repair,
        "lesson": mission.lesson,
        "worried": world.worried,
        "dialogue": world.talking,
        "repaired": world.repaired,
        "safe": world.safe,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
robot(X) :- robot_name(X).
dialogue :- asks(hero), answers(helper), offers_help(robot).
humor :- joke(robot).
repair :- dialogue, clue_found, tool_used.
safe :- repair.
#show dialogue/0.
#show humor/0.
#show repair/0.
#show safe/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero_name", "christian"),
        asp.fact("helper_name", "nova"),
        asp.fact("robot_name", "bloop"),
        asp.fact("asks", "hero"),
        asp.fact("answers", "helper"),
        asp.fact("offers_help", "robot"),
        asp.fact("joke", "robot"),
        asp.fact("clue_found"),
        asp.fact("tool_used"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


def asp_verify() -> int:
    if not asp_available():
        print("ASP verification unavailable: clingo is not installed.")
        return 1
    import asp
    model = asp.one_model(asp_program())
    found = {str(atom) for atom in model}
    expected = {"dialogue", "humor", "repair", "safe"}
    if expected.issubset(found):
        print("OK: ASP twin reaches dialogue, humor, repair, and safety.")
        return 0
    print("MISMATCH: ASP twin did not reach the expected state.")
    return 1


def prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a humorous space adventure about {p.hero} repairing a problem with {p.helper} and {p.robot}.",
        f"Tell a child-friendly story in {p.place} where dialogue reveals a useful clue.",
        f"Write an ending where the crew safely shares {p.prize} after fixing the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    m = world.mission
    return [
        QAItem(
            question=f"What trouble interrupted {p.hero}'s mission?",
            answer=f"{m.trouble.capitalize()} Christian and the crew were worried because the problem threatened their space adventure.",
        ),
        QAItem(
            question="What clue helped the crew understand the problem?",
            answer=f"They noticed that {m.clue}. This clue pointed them toward the real cause instead of a frightening guess.",
        ),
        QAItem(
            question="How did dialogue help the crew?",
            answer=f"Christian asked for careful observations, {p.helper} shared the clue, and {p.robot} offered to test it. Their conversation became a shared repair plan.",
        ),
        QAItem(
            question="How did humor help without replacing careful work?",
            answer=f"{p.robot} made a joke about the trouble, which helped everyone breathe and keep working. The crew still checked the clue and completed the repair.",
        ),
        QAItem(
            question="What final image showed that the mission was safe?",
            answer=f"{m.ending.capitalize()} The crew could then enjoy {p.prize} together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is a conversation in which characters speak and listen to one another.",
        ),
        QAItem(
            question="Why can humor help during a difficult task?",
            answer="A gentle joke can help people relax and feel hopeful, but careful thinking and safe actions are still needed.",
        ),
        QAItem(
            question="What does an astronaut do?",
            answer="An astronaut travels or works in space and follows careful procedures to stay safe.",
        ),
        QAItem(
            question=f"What is a moon base?",
            answer=f"A moon base is a place where people can live, work, and study on the Moon, such as {p.place}.",
        ),
        QAItem(
            question="Why should a crew listen to clues?",
            answer="Clues provide evidence about what happened, so a crew can solve a problem instead of acting on a guess.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in [world.hero, world.helper, world.robot]:
        lines.append(f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"state: worried={world.worried} dialogue={world.talking} "
        f"repaired={world.repaired} safe={world.safe}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="Christian",
        helper="Nova",
        robot="Bloop",
        place="the little moon base",
        craft="the Starling",
        prize="warm cinnamon buns",
    ),
    StoryParams(
        hero="Christian",
        helper="Mara",
        robot="Orbit",
        place="the crater laboratory",
        craft="the Blue Rocket",
        prize="apple mooncakes",
    ),
]


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
        print(asp_program("#show dialogue/0.\n#show humor/0.\n#show repair/0.\n#show safe/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        if not asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        if args.all:
            header = f"### {sample.params.hero} and the crew at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
