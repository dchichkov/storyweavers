#!/usr/bin/env python3
"""A cautionary space adventure about genius, teamwork, and a repaired mission."""

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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Mission:
    id: str
    discovery: str
    danger: str
    mistake: str
    clue: str
    repair: str
    rescue: str
    ending: str


@dataclass
class StoryParams:
    mission: str = "ice_moon"
    name: str = "Luna"
    helper_name: str = "Orion"
    opening: int = 0
    caution: int = 0
    reflection: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


MISSIONS = {
    "ice_moon": Mission(
        "ice_moon",
        "The starship Lantern reached a small ice moon whose blue cracks glowed beneath the frozen ground.",
        "A sudden tremor trapped the exploration rover beyond the landing beacon while a storm of glittering ice rushed toward it.",
        "Luna, the ship's young genius, tried to calculate a shortcut alone and sent the rover toward a field of thin ice.",
        "Orion noticed that the moon's cracks pulsed in the same rhythm as the rover's weak signal.",
        "They slowed down, mapped the pulses together, and used the rover's mirror to bounce a safe signal between the cracks.",
        "The rover followed the reflected lights back to solid ground just before the storm swept over the thin ice.",
        "The repaired beacon shone beside a calm blue crack while the Lantern rose toward the stars.",
    ),
    "silent_comet": Mission(
        "silent_comet",
        "The Lantern found a comet carrying a garden of silver seeds inside its warm tail.",
        "The ship's engines became silent near the comet, and the vessel began drifting toward a dark pocket of space.",
        "Luna switched every control at once, making the ship spin faster instead of slowing it.",
        "Orion heard tiny clicks from the seed garden and realized the comet's dust was striking the hull in a steady pattern.",
        "They stopped guessing, matched the clicks with gentle thruster taps, and turned the ship away from the dark pocket.",
        "The silver seeds floated safely past the windows as the engines began to hum again.",
    ),
    "red_nebula": Mission(
        "red_nebula",
        "The crew entered a red nebula where clouds of glowing dust made new shapes every minute.",
        "Their navigation screen showed three routes, but only one led out before the ship's air filter filled with red dust.",
        "Luna trusted the brightest route because it looked fastest, though its light came from a dangerous swirling cloud.",
        "Orion found old probe marks hidden beneath the dust and saw that the safest route had the quietest glow.",
        "They compared the marks, chose the slower path, and sealed the filter vents before moving.",
        "The Lantern slipped through the quiet corridor and left the nebula with clean air and a bright view of home.",
    ),
}

OPENINGS = [
    "The mission began with a discovery no star chart had promised.",
    "The Lantern sailed quietly between the planets until its instruments blinked.",
    "Beyond the last familiar moon, the crew found a problem waiting in the dark.",
    "Space looked peaceful, but peaceful places can still hide sharp surprises.",
]

CAUTIONS = [
    '"Being a genius does not mean solving everything alone," said {helper}.',
    '"A clever idea needs a careful test," {helper} reminded {hero}.',
    '"Let us check the danger before we chase the answer," said {helper}.',
    '"Slow thinking can save a fast ship," {helper} told {hero}.',
]

REFLECTIONS = [
    "Luna learned that brilliance was strongest when it listened to evidence.",
    "The safest answer was not the quickest-looking answer.",
    "A true genius can change a plan when new facts appear.",
    "Care was not the enemy of discovery; it was what brought discovery home.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary space adventure about genius.")
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("--name")
    parser.add_argument("--helper-name")
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
    name = getattr(args, "name", None) or rng.choice(["Luna", "Nova", "Mira", "Sol"])
    helpers = [x for x in ["Orion", "Tavi", "Juno", "Pax"] if x != name]
    helper = getattr(args, "helper_name", None) or rng.choice(helpers)
    return StoryParams(
        mission=getattr(args, "mission", None) or rng.choice(list(MISSIONS)),
        name=name,
        helper_name=helper,
        opening=rng.randrange(len(OPENINGS)),
        caution=rng.randrange(len(CAUTIONS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def tell(params: StoryParams) -> World:
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")
    if params.name == params.helper_name:
        raise StoryError("The explorer and helper need different names.")

    mission = MISSIONS[params.mission]
    world = World(params)
    hero = world.add(Entity(params.name, "explorer", params.name, {"genius": 1.0, "risk": 0.0, "caution": 0.0}))
    helper = world.add(Entity(params.helper_name, "navigator", params.helper_name, {"skill": 1.0, "trust": 1.0}))
    ship = world.add(Entity("lantern", "ship", "the Lantern", {"fuel": 1.0, "air": 1.0}))

    world.facts.update(hero=hero, helper=helper, ship=ship, mission=mission)
    opening = OPENINGS[params.opening % len(OPENINGS)]
    caution = CAUTIONS[params.caution % len(CAUTIONS)].format(hero=hero.label, helper=helper.label)
    reflection = REFLECTIONS[params.reflection % len(REFLECTIONS)]

    world.say(f"{opening} {mission.discovery} {hero.label}, a young genius explorer aboard the Lantern, studied the strange signals.")
    world.say(f"{helper.label} checked the navigation panel while {hero.label} filled the screen with brilliant calculations.")
    world.para()

    hero.meters["risk"] += 1.0
    world.say(f"{mission.danger} {mission.mistake}")
    world.say(f'"I know the answer," {hero.label} said. {caution}')
    world.para()

    hero.meters["caution"] += 1.0
    helper.meters["trust"] += 1.0
    world.say(f"{hero.label} stopped and looked again. {mission.clue}")
    world.say(f'"You found a fact I missed," said {hero.label}. "{helper.label}, help me test the safer plan."')
    world.say(f'"Together," {helper.label} replied. {mission.repair}')
    world.para()

    hero.meters["risk"] = 0.0
    hero.meters["caution"] += 1.0
    world.fired.update({"noticed_clue", "accepted_help", "repaired_mission"})
    world.say(f"{mission.rescue} The crew cheered, not because {hero.label} had been perfect, but because the genius explorer had been willing to learn.")
    world.say(f"{reflection} {mission.ending}")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    return [
        "Write a child-friendly cautionary space adventure in which genius must be guided by care.",
        f"Show how {hero.label} faces this danger: {mission.danger}",
        f"Use the clue and repair to create a hopeful ending: {mission.clue} {mission.repair}",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            f"Why did {hero.label}'s first idea cause trouble?",
            f"{hero.label} rushed into a shortcut without checking the danger, so the plan made the mission less safe.",
        ),
        QAItem(
            "What clue changed the mission?",
            mission.clue,
        ),
        QAItem(
            f"How did {hero.label} and {helper.label} repair the mission?",
            mission.repair,
        ),
        QAItem(
            "What caution does the adventure teach?",
            "Genius is valuable, but careful observation, teamwork, and a willingness to change plans make genius safer and more useful.",
        ),
        QAItem(
            "What image ends the story?",
            mission.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a genius?", "A genius is someone with exceptional ability or insight in an area, but even a genius benefits from checking ideas and listening to others."),
        QAItem("What is caution?", "Caution means noticing possible danger and choosing a careful action before moving ahead."),
        QAItem("Why do space crews work as teams?", "Space crews work as teams because different people can notice different facts, share decisions, and help keep a mission safe."),
        QAItem("What is a spacecraft?", "A spacecraft is a vehicle designed to travel beyond Earth's atmosphere."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        lines.append(f"  {entity.label}: kind={entity.kind}, meters={meters}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
danger_seen(hero) :- hero(hero), risk(hero).
careful_genius(hero) :- genius(hero), danger_seen(hero), accepts_help(hero), clue_checked(hero).
mission_safe(hero) :- careful_genius(hero), repaired(hero).
#show danger_seen/1.
#show careful_genius/1.
#show mission_safe/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "luna"),
        asp.fact("genius", "luna"),
        asp.fact("risk", "luna"),
        asp.fact("accepts_help", "luna"),
        asp.fact("clue_checked", "luna"),
        asp.fact("repaired", "luna"),
    ])


def asp_program(show: str = "#show danger_seen/1. #show careful_genius/1. #show mission_safe/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    symbols = asp.one_model(asp_program())
    actual = {str(symbol) for symbol in symbols}
    expected = {"danger_seen(luna)", "careful_genius(luna)", "mission_safe(luna)"}
    if actual == expected:
        sample = generate(StoryParams())
        if not sample.story or "genius" not in sample.story.lower():
            print("Generated story exercise failed.")
            return 1
        print("OK: ASP twin matches the Python caution gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(actual))
    print("  expected:", sorted(expected))
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

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp
        print("\n".join(sorted(str(atom) for atom in asp.one_model(asp_program()))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for mission in MISSIONS:
            params = StoryParams(mission=mission, name="Luna", helper_name="Orion")
            params.seed = base_seed
            samples.append(generate(params))
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
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
