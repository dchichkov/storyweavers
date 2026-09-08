#!/usr/bin/env python3
"""A cautionary space adventure about a hiccup, careful teamwork, and a happy ending."""

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


SETTINGS = {
    "moon": "the silver moon station",
    "nebula": "the violet nebula",
    "asteroid": "the little asteroid outpost",
}

CAPTAINS = ("Luna", "Mira", "Sol", "Nova")
ROBOTS = ("Pip", "Orbit", "Tiko", "Beep")
SUPPLIES = ("star apples", "moon muffins", "comet carrots", "glow berries")


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str = SETTINGS["moon"]
    captain: str = "Luna"
    robot: str = "Pip"
    supply: str = "star apples"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mission:
    name: str
    danger: str
    clue: str
    careless_choice: str
    captain_job: str
    robot_job: str
    safe_method: str
    result: str
    ending_image: str


MISSIONS = (
    Mission(
        "the blinking beacon",
        "the rescue beacon blinked weakly while a meteor shower approached",
        "its power cable had slipped beside a loose silver latch",
        "rush outside and grab the beacon with bare gloves",
        "read the storm map from inside the airlock",
        "secure the cable with the spare clamp",
        "wait for a quiet gap, lock the airlock, and use the long safety pole",
        "the beacon shone steadily before the meteors reached the station",
        "a bright blue signal danced safely above the moon dust",
    ),
    Mission(
        "the drifting supply pod",
        "the supply pod floated toward a dark crater",
        "one guide rope was wrapped around a harmless antenna",
        "fly after it at full speed without checking the rope",
        "watch the pod's path through the navigation window",
        "untangle the rope and pull with the winch",
        "the pod glided back beside the docking rail",
        "the rescued supplies rested beneath a warm cabin light",
    ),
    Mission(
        "the sleepy rover",
        "the rover stopped at the edge of a cracked ice bridge",
        "its wheels were clear, but its warning lamp showed thin ice ahead",
        "tell the rover to hurry across before the bridge broke",
        "scan the bridge with the small radar",
        "mark a route around the strong ridge",
        "the rover carried its cargo safely around the crack",
        "two rover tracks curved home beside a row of orange flags",
    ),
    Mission(
        "the wandering moon kite",
        "a research kite tugged free and sailed toward a spinning satellite",
        "its bright tail had caught on a harmless antenna loop",
        "jump after the kite without fastening a safety line",
        "track the satellite's slow turn",
        "reel in the kite from the tether platform",
        "the kite came back without touching the satellite",
        "its silver tail waved from a safe hook beside the window",
    ),
)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary space adventure story world.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--robot", choices=ROBOTS)
    parser.add_argument("--supply", choices=SUPPLIES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(list(SETTINGS))
    captain = args.captain or rng.choice(CAPTAINS)
    robot = args.robot or rng.choice(ROBOTS)
    if robot == captain:
        robot = rng.choice([name for name in ROBOTS if name != captain])
    return StoryParams(
        setting=SETTINGS[setting_key],
        captain=captain,
        robot=robot,
        supply=args.supply or rng.choice(SUPPLIES),
    )


def choose_mission(params: StoryParams) -> Mission:
    seed = params.seed if params.seed is not None else 0
    return MISSIONS[seed % len(MISSIONS)]


def tell(params: StoryParams) -> World:
    if params.captain == params.robot:
        raise StoryError("The captain and robot must have different names.")
    if params.setting not in SETTINGS.values():
        raise StoryError("The setting must be one of the registered space locations.")
    if params.supply not in SUPPLIES:
        raise StoryError("The supply must be one of the registered space supplies.")

    world = World(params)
    captain = world.add(Entity(
        id="captain",
        kind="character",
        label=params.captain,
        role="captain",
        meters={"air": 1.0, "alertness": 1.0, "risk": 0.0},
        memes={"courage": 1.0, "care": 1.0},
        traits=["curious", "learning-caution"],
    ))
    robot = world.add(Entity(
        id="robot",
        kind="character",
        label=params.robot,
        role="helper robot",
        meters={"battery": 1.0, "signal": 1.0},
        memes={"friendship": 1.0, "care": 1.0},
        traits=["helpful", "careful"],
    ))
    supply = world.add(Entity(
        id="supply",
        kind="thing",
        label=params.supply,
        role="mission supply",
        meters={"value": 1.0},
        memes={},
        traits=["fragile"],
    ))

    mission = choose_mission(params)
    place = params.setting

    world.say(f"Captain {captain.label} and {robot.label} were exploring {place}.")
    world.say(
        f"They carried {supply.label} for the station kitchen when they heard a warning chime: "
        f"{mission.danger}."
    )
    world.say(
        f"“We need to help quickly,” said {captain.label}. “But space rewards careful steps.”"
    )
    world.say(
        f"{robot.label} raised one shiny finger. “A hiccup in a plan can become a big problem if we hurry.”"
    )

    world.para()
    world.say(f"Just then, {captain.label} had a tiny hiccup. “Hic!”")
    world.say(
        f"The hiccup made the captain press the scanner twice, and the screen showed a false red flash. "
        f"{robot.label} did not panic. {robot.label} checked the panel and found that {mission.clue}."
    )
    world.say(
        f"“I almost chose to {mission.careless_choice},” admitted {captain.label}."
    )
    world.say(
        f"“That would be risky,” said {robot.label}. “Let us pause, look, and make a safe plan.”"
    )
    captain.meters["risk"] += 1.0
    captain.memes["caution"] = 1.0

    world.para()
    world.say(f"They agreed that {mission.safe_method}.")
    world.say(
        f"{captain.label} would {mission.captain_job}, while {robot.label} would {mission.robot_job}."
    )
    world.say(
        f"The hiccup faded after {captain.label} took one slow breath. Then the two space friends "
        f"worked together and {mission.result}."
    )
    captain.meters["risk"] = 0.0
    captain.meters["alertness"] += 1.0
    robot.meters["battery"] -= 0.1
    captain.memes["courage"] += 1.0
    robot.memes["friendship"] += 1.0

    world.para()
    world.say(
        f"Back aboard the station, they placed the {supply.label} safely on the table."
    )
    world.say(
        f"“A hiccup is not a disaster,” said {captain.label}. “It is a reminder to slow down.”"
    )
    world.say(
        f"{robot.label} beeped happily. “And a warning is useful when we listen to it.”"
    )
    world.say(
        f"They shared a snack while {mission.ending_image}."
    )

    world.facts.update(
        captain=captain,
        robot=robot,
        supply=supply,
        place=place,
        mission=mission.name,
        danger=mission.danger,
        clue=mission.clue,
        careless_choice=mission.careless_choice,
        captain_job=mission.captain_job,
        robot_job=mission.robot_job,
        safe_method=mission.safe_method,
        result=mission.result,
        ending_image=mission.ending_image,
        hiccup=True,
        caution=True,
        happy_ending=True,
        dialogue=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    captain = facts["captain"].label
    robot = facts["robot"].label
    return [
        f"Write a child-friendly space adventure about {captain} and {robot} solving {facts['mission']}.",
        f"Include a funny hiccup, a cautionary choice, dialogue, and a happy ending involving {facts['result']}.",
        "Show why pausing and checking danger is wiser than rushing in space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    captain = facts["captain"].label
    robot = facts["robot"].label
    supply = facts["supply"].label
    return [
        QAItem(
            question=f"What problem did {captain} and {robot} face?",
            answer=f"They faced {facts['danger']}.",
        ),
        QAItem(
            question="How did the hiccup affect the mission?",
            answer=(
                f"The hiccup made {captain} press the scanner twice and briefly showed a false red flash, "
                "so the friends paused instead of rushing."
            ),
        ),
        QAItem(
            question=f"What clue helped {captain} and {robot} understand the danger?",
            answer=f"They discovered that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did {captain} and {robot} solve the problem?",
            answer=(
                f"They decided to {facts['safe_method']}. "
                f"{captain} worked to {facts['captain_job']}, while {robot} worked to {facts['robot_job']}."
            ),
        ),
        QAItem(
            question=f"What proved that the ending was happy for the {supply}?",
            answer=f"The mission succeeded because {facts['result']}, and afterward {facts['ending_image']}.",
        ),
        QAItem(
            question="What cautionary lesson did the space friends learn?",
            answer="They learned that a pause, a check, and a safety plan can prevent a small hiccup from becoming a dangerous mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should astronauts follow safety rules?",
            answer="Astronauts should follow safety rules because space can be dangerous and careful steps protect people and equipment.",
        ),
        QAItem(
            question="What is a hiccup?",
            answer="A hiccup is a small, sudden movement or interruption that can make someone pause.",
        ),
        QAItem(
            question="Why is teamwork useful during an adventure?",
            answer="Teamwork is useful because friends can notice different clues, share jobs, and help one another make safer choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    lines.append(f"facts: {world.facts['mission']}, caution={world.facts['caution']}, hiccup={world.facts['hiccup']}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_setting/1.
#show valid_supply/1.
valid_setting(moon).
valid_setting(nebula).
valid_setting(asteroid).
valid_supply(star_apples).
valid_supply(moon_muffins).
valid_supply(comet_carrots).
valid_supply(glow_berries).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("valid_setting", key) for key in SETTINGS]
    lines.extend(asp.fact("valid_supply", value.replace(" ", "_")) for value in SUPPLIES)
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        settings = sorted(set(asp.atoms(model, "valid_setting")))
        supplies = sorted(set(asp.atoms(model, "valid_supply")))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1

    expected_settings = sorted((key,) for key in SETTINGS)
    expected_supplies = sorted((value.replace(" ", "_"),) for value in SUPPLIES)
    if settings != expected_settings or supplies != expected_supplies:
        print("MISMATCH: ASP registry facts differ from Python registries.")
        return 1

    for seed in range(8):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if not sample.story or "hiccup" not in sample.story.lower():
            print("MISMATCH: generated story failed the hiccup check.")
            return 1

    print("OK: ASP registries match Python and generated stories pass.")
    return 0


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
    StoryParams(setting=SETTINGS["moon"], captain="Luna", robot="Pip", supply="star apples", seed=0),
    StoryParams(setting=SETTINGS["nebula"], captain="Mira", robot="Orbit", supply="moon muffins", seed=1),
    StoryParams(setting=SETTINGS["asteroid"], captain="Sol", robot="Tiko", supply="glow berries", seed=2),
    StoryParams(setting=SETTINGS["moon"], captain="Nova", robot="Beep", supply="comet carrots", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_setting/1.\n#show valid_supply/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Registered settings:")
        for key, value in SETTINGS.items():
            print(f"  {key}: {value}")
        print("Registered supplies:")
        for supply in SUPPLIES:
            print(f"  {supply}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 50):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.captain} and {sample.params.robot} at {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
