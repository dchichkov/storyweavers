#!/usr/bin/env python3
"""
A comic storyworld about a slippery object, a brave rescue, and kindness.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"balance": 1.0, "worry": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.0, "bravery": 0.0, "comedy": 0.0})
    inventory: list[str] = field(default_factory=list)


@dataclass
class SlipperyThing:
    label: str
    material: str
    location: str
    slippery: bool = True
    rescued: bool = False
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"roll": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"mischief": 1.0})


@dataclass
class Setting:
    place: str
    surface: str


@dataclass
class StoryParams:
    place: str = "the village washhouse"
    surface: str = "a freshly soaped floor"
    hero_name: str = "Luna"
    hero_species: str = "mouse"
    friend_name: str = "Bram"
    friend_species: str = "duck"
    object_name: str = "the slippery soap"
    scenario_id: int = 0
    opening_mode: int = 0
    dialogue_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    premise: str
    problem: str
    failed_attempt: str
    clue: str
    action: str
    resolution: str
    lesson: str
    image: str


SCENARIOS = (
    Scenario(
        "Luna had promised to replicate the village's famous moon-shaped soap for the fair.",
        "The first replica was so slippery that it shot across the washhouse and headed for an open drain.",
        "Luna chased it, slipped, and landed inside an empty laundry basket",
        "the soap slowed whenever it touched a dry towel",
        "spread towels into a soft path while Bram blocked the drain with a bucket",
        "The replica stopped safely, and Luna gave the first soap to Bram for helping.",
        "kindness means making room for a helper instead of pretending to manage alone",
        "the moon-shaped soap rested on a towel while the laundry basket wore Luna like a hat",
    ),
    Scenario(
        "Luna wanted to replicate the baker's shiny seed bun as a tiny clay prize.",
        "The wet clay bun became slippery and rolled beneath a table during judging.",
        "reached under the table with one paw and accidentally pushed it farther",
        "a trail of flour showed that the clay rolled toward the warm oven, not the door",
        "asked Bram to watch the oven while Luna used a long wooden spoon to guide the bun out",
        "They saved the replica before it baked hard, then let Bram choose its cheerful button eyes.",
        "bravery works best when it listens to careful advice",
        "the rescued bun sat on a ribbon, wearing two button eyes and one proud floury grin",
    ),
    Scenario(
        "For the school play, Luna tried to replicate the mayor's enormous golden hat.",
        "The paper hat slid down the stage ramp and carried a nervous chick with it.",
        "grabbed the hat and spun around until both Luna and the hat looked dizzy",
        "the hat's slippery lining caught on a strip of soft felt",
        "held the felt flat while Bram coaxed the chick toward the safe side of the ramp",
        "The chick was safe, and the hat became a comic prop instead of a dangerous one.",
        "kindness notices who needs help before saving the prized object",
        "the mayor's replica hat ended up on a broom, where it bowed to the audience",
    ),
    Scenario(
        Scenario(
            "Luna had made a replica of the town bell from polished pudding mold.",
            "The slippery bell slid down the hill whenever anyone tried to carry it to the parade.",
            "put it in a wheelbarrow, which immediately rolled faster than Luna",
            "the bell stopped beside patches of rough moss",
            "laid moss in a line while Bram held the wheelbarrow handles steady",
            "They reached the parade, where Luna let Bram ring the pudding bell first.",
            "bravery can include trusting a friend with the moment you wanted",
            "the pudding bell wobbled on the parade cart and made everyone laugh before the real bell rang",
        )
    ),
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, entity: object) -> object:
        self.entities[eid] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _render(text: str, hero: Character, friend: Character) -> str:
    return text.format(hero=hero.name, friend=friend.name)


def _opening(mode: int, hero: Character, friend: Character, setting: Setting, scenario: Scenario) -> str:
    openings = (
        f"At {setting.place}, {hero.name} the {hero.species} announced, 'Today I will replicate something magnificent.' {friend.name} the {friend.species} wisely took one step away.",
        f"The day began at {setting.place}, where {hero.name} had a plan, {friend.name} had a towel, and neither had yet discovered why the floor was {setting.surface}.",
        f"{hero.name} arrived at {setting.place} carrying a proud idea and a very small sense of danger. {friend.name} arrived carrying common sense.",
        f"At {setting.place}, {hero.name} lifted a paw and declared, 'Nothing can go wrong.' The slippery object chose that moment to wobble.",
    )
    return openings[mode % len(openings)] + " " + _render(scenario.premise, hero, friend)


def _dialogue(mode: int, hero: Character, friend: Character) -> tuple[str, str]:
    lines = (
        (f"'I can catch it!' cried {hero.name}.", f"'You can also ask for help,' said {friend.name}."),
        (f"'Stand back! I have a plan!' said {hero.name}.", f"'Is the plan supposed to involve that basket?' asked {friend.name}."),
        (f"'What if I fail?' whispered {hero.name}.", f"'Then we will try a kinder, less slippery way,' said {friend.name}."),
        (f"'I meant to do that,' said {hero.name} from the floor.", f"'Of course,' said {friend.name}. 'The floor looked very surprised.'"),
    )
    return lines[mode % len(lines)]


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("hero and friend names must not be empty")
    if params.hero_name == params.friend_name:
        raise StoryError("hero and friend must have different names")
    if not params.place.strip():
        raise StoryError("place must not be empty")

    world = World(Setting(params.place, params.surface))
    hero = world.add(
        "hero",
        Character(params.hero_name, params.hero_species, "inventor"),
    )
    friend = world.add(
        "friend",
        Character(params.friend_name, params.friend_species, "helper"),
    )
    thing = world.add(
        "replica",
        SlipperyThing(params.object_name, "soap-clay", params.place, owner=hero.name),
    )
    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]

    hero.memes["comedy"] = 1.0
    hero.meters["worry"] = 0.3
    friend.memes["kindness"] = 0.5

    world.say(_opening(params.opening_mode, hero, friend, world.setting, scenario))
    world.say("A replica is a new copy made to resemble something else. This replica was also extremely slippery.")

    world.para()
    world.say(_render(scenario.problem, hero, friend))
    world.say(f"At first, {hero.name} {_render(scenario.failed_attempt, hero, friend)}.")
    first, second = _dialogue(params.dialogue_mode, hero, friend)
    world.say(first + " " + second)
    world.say(f"{friend.name} pointed out that {_render(scenario.clue, hero, friend)}.")

    world.para()
    world.say(f"{hero.name} took a breath and chose bravery without choosing foolishness.")
    world.say(f"Together, {hero.name} and {friend.name} {_render(scenario.action, hero, friend)}.")
    world.say(_render(scenario.resolution, hero, friend))

    thing.rescued = True
    thing.location = f"the safe corner of {params.place}"
    hero.inventory.append("a dry towel")
    hero.meters["worry"] = 0.0
    hero.memes["bravery"] = 1.0
    hero.memes["kindness"] = 1.0
    friend.memes["kindness"] = 1.0
    friend.memes["bravery"] = 1.0
    world.events.extend(["replica_made", "slippery_danger_seen", "help_requested", "object_rescued"])

    world.para()
    endings = (
        f"{hero.name} learned that {_render(scenario.lesson, hero, friend)}.",
        f"'Next time, I will ask sooner,' {hero.name} told {friend.name}. That was brave, and it was kind.",
        f"The adventure left {hero.name} with a useful rule: {_render(scenario.lesson, hero, friend)}.",
        f"{friend.name} smiled. 'Your replica is funny,' said {friend.name}, 'but your kindness is the best part.'",
    )
    images = (
        f"At the end, {_render(scenario.image, hero, friend)}.",
        f"When the laughter settled, {_render(scenario.image, hero, friend)}.",
        f"By sunset, {_render(scenario.image, hero, friend)}.",
        f"The final picture was simple: {_render(scenario.image, hero, friend)}.",
    )
    world.say(endings[params.ending_mode % len(endings)])
    world.say(images[(params.ending_mode + 1) % len(images)])

    world.facts.update(
        hero=hero,
        friend=friend,
        thing=thing,
        scenario=scenario,
        problem=_render(scenario.problem, hero, friend),
        clue=_render(scenario.clue, hero, friend),
        action=_render(scenario.action, hero, friend),
        resolution=_render(scenario.resolution, hero, friend),
        lesson=_render(scenario.lesson, hero, friend),
        image=_render(scenario.image, hero, friend),
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    hero: Character = world.facts["hero"]
    friend: Character = world.facts["friend"]
    f = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a comedy about {hero.name} replicating something slippery at {params.place}.",
            f"Show how {hero.name} uses bravery and {friend.name}'s kindness after this clue: {f['clue']}",
            f"End with a funny image proving that the slippery replica was rescued: {f['image']}",
        ],
        story_qa=[
            QAItem(
                f"What problem did {hero.name} face?",
                f"{hero.name} faced this problem: {f['problem']}.",
            ),
            QAItem(
                f"What clue helped {hero.name} and {friend.name}?",
                f"They learned that {f['clue']}.",
            ),
            QAItem(
                f"How did the friends rescue the replica?",
                f"They worked together so that {f['action']}.",
            ),
            QAItem(
                f"What did {hero.name} learn?",
                f"{hero.name} learned that {f['lesson']}.",
            ),
            QAItem(
                "Was the slippery replica rescued?",
                f"Yes. The replica was rescued and placed in {f['thing'].location}.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a replica?",
                "A replica is a new copy made to look like an original object.",
            ),
            QAItem(
                "What does slippery mean?",
                "Slippery means hard to hold or stand on because something slides easily.",
            ),
            QAItem(
                "What is kindness?",
                "Kindness means noticing another person's needs and choosing to help with care.",
            ),
            QAItem(
                "What is bravery?",
                "Bravery means taking a sensible, caring action even when something feels frightening.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    hero: Character = world.entities["hero"]
    friend: Character = world.entities["friend"]
    thing: SlipperyThing = world.entities["replica"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting.place}",
            f"surface: {world.setting.surface}",
            f"hero: {hero.name} {hero.species} meters={hero.meters} memes={hero.memes}",
            f"friend: {friend.name} {friend.species} meters={friend.meters} memes={friend.memes}",
            f"replica: label={thing.label} slippery={thing.slippery} rescued={thing.rescued} location={thing.location}",
            f"events: {world.events}",
        ]
    )


ASP_RULES = r"""
hero(h).
friend(f).
replica(r).
slippery(r).
rescued(r) :- towel_used, helper_blocked.
kindness(h) :- rescued(r).
kindness(f) :- rescued(r).
bravery(h) :- rescued(r).
bravery(f) :- rescued(r).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "h"),
            asp.fact("friend", "f"),
            asp.fact("replica", "r"),
            asp.fact("slippery", "r"),
            asp.fact("towel_used"),
            asp.fact("helper_blocked"),
        ]
    )


def asp_program(show: str = "#show rescued/1. #show kindness/1. #show bravery/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if ("r",) not in set(asp.atoms(model, "rescued")):
        print("MISMATCH: ASP did not derive rescued(r).")
        return 1
    if len(asp.atoms(model, "kindness")) != 2 or len(asp.atoms(model, "bravery")) != 2:
        print("MISMATCH: ASP did not derive kindness and bravery for both friends.")
        return 1
    sample = generate(StoryParams(seed=7))
    if "slippery" not in sample.story.lower() or "kind" not in sample.story.lower():
        print("MISMATCH: generated story lacks required narrative features.")
        return 1
    print("OK: Python and ASP agree that the slippery replica is rescued through kindness and bravery.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Comedy storyworld about a slippery replica.")
    parser.add_argument("--place", default=None)
    parser.add_argument("--surface", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
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
        place=args.place or rng.choice(
            ["the village washhouse", "the school stage", "the sunny fairground", "the parade hill"]
        ),
        surface=args.surface or rng.choice(
            ["a freshly soaped floor", "a polished ramp", "a wet wooden table", "a patch of dewy grass"]
        ),
        hero_name=rng.choice(["Luna", "Mabel", "Pip", "Tansy"]),
        hero_species=rng.choice(["mouse", "fox", "rabbit", "squirrel"]),
        friend_name=rng.choice(["Bram", "Clover", "Nico", "Dot"]),
        friend_species=rng.choice(["duck", "badger", "hedgehog", "goat"]),
        object_name=rng.choice(["the slippery soap", "the slippery clay bun", "the slippery paper hat", "the slippery pudding bell"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        opening_mode=rng.randrange(4),
        dialogue_mode=rng.randrange(4),
        ending_mode=rng.randrange(4),
        seed=args.seed,
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        model = asp.one_model(asp_program())
        print("rescued:", asp.atoms(model, "rescued"))
        print("kindness:", asp.atoms(model, "kindness"))
        print("bravery:", asp.atoms(model, "bravery"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(place="the village washhouse", surface="a freshly soaped floor", scenario_id=0),
            StoryParams(place="the school stage", surface="a polished ramp", scenario_id=1),
            StoryParams(place="the sunny fairground", surface="a wet wooden table", scenario_id=2),
            StoryParams(place="the parade hill", surface="a patch of dewy grass", scenario_id=3),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(0, args.n))
        ]

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
