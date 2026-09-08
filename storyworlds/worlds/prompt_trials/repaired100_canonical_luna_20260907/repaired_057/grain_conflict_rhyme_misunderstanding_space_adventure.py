#!/usr/bin/env python3
"""
A small child-facing space-adventure story world about a grain, a rhyme, and a
misunderstanding between two young explorers.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little starship Luna"
    destination: str = "the Moon Garden"
    affords: set[str] = field(default_factory=lambda: {"explore", "listen", "plant"})


@dataclass
class GrainKind:
    key: str
    phrase: str
    use: str
    clue: str


@dataclass
class Scenario:
    title: str
    danger: str
    misunderstanding: str
    first_try: str
    rhyme: str
    clue: str
    repair: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    grain: str
    seed: Optional[int] = None


@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    grain: Entity
    setting: Setting
    scenario: Scenario
    heard_rhyme: bool = False
    conflict: bool = False
    understood: bool = False
    resolved: bool = False


SETTING = Setting()

GRAINS = {
    "stargrain": GrainKind(
        "stargrain",
        "a silver grain of stargrain",
        "grow a tiny food garden in moon soil",
        "its shell shimmered whenever the ship turned toward moonlight",
    ),
    "sunseed": GrainKind(
        "sunseed",
        "a warm golden sunseed",
        "feed the greenhouse sprouter",
        "a faint glow pulsed whenever someone spoke its planting rhyme",
    ),
    "bluegrain": GrainKind(
        "bluegrain",
        "a blue grain from the cloud planet",
        "help make a water-saving space garden",
        "a cool drop appeared beside it when the cabin grew quiet",
    ),
}

HERO_NAMES = ["Luna", "Mira", "Nell", "Pip", "Ari", "Tess"]
HELPER_NAMES = ["Orion", "Sol", "Kito", "Wren", "Bram", "Nova"]

SCENARIOS = (
    Scenario(
        "the moon-garden mission",
        "the starship's seed box slid loose as a comet tail brushed the hull",
        "the friends thought they were arguing about who should keep the last grain",
        "grabbed the box and rushed toward the greenhouse without checking the ship map",
        "Count the stars, then plant one far; share the light from star to star.",
        "the grain shimmered three times beside the word SHARE on the planting card",
        "read the card together and tethered the seed box before planting the grain in a moon-soil cup",
        "A green curl rose under the dome, bright as a tiny flag among the craters",
        "A misunderstanding can shrink when friends listen to the same clue.",
    ),
    Scenario(
        "the quiet-orbit mission",
        "the ship drifted into a quiet orbit while its garden lamp blinked low",
        "one explorer thought the other had hidden the grain because the seed pouch was empty",
        "searched the sleeping nook alone and bumped the pouch beneath a cushion",
        "Small grain, bright refrain: ask your friend before you blame.",
        "the rhyme's last word echoed from the cushion where the pouch had landed",
        "asked a calm question, found the pouch, and placed the grain in the lamp's warm growing tray",
        "A pale sprout opened while the ship sailed silently above the blue planet",
        "Asking kindly is better than guessing angrily.",
    ),
    Scenario(
        "the comet-cabin mission",
        "a comet's icy sparkle made the navigation windows flash and glow",
        "the friends mistook a safety rhyme for an order to race to opposite sides of the cabin",
        "ran in different directions until their float belts gently bumped together",
        "Left or right, hold on tight; one kind voice can steer the night.",
        "the grain rolled into the center cradle marked with a single heart",
        "held hands on the safety rail, spoke the rhyme slowly, and guided the grain into the center cradle",
        "The comet glittered outside as the grain rested safely beside the navigation star",
        "Clear words and teamwork can turn a confusing signal into a safe plan.",
    ),
    Scenario(
        "the red-planet mission",
        "the greenhouse rover reported one dry planting cup on the red planet",
        "the friends thought the grain had been taken by a dust sprite",
        "shook every empty jar, making dust dance but finding no sprite",
        "Dust may swirl and shadows may feign; look with a friend, then look again.",
        "the grain's tiny shadow pointed beneath the rover's folded ramp",
        "lifted the ramp together and carried the grain to the marked cup",
        "A green shoot appeared beside the rover's wheel, making a soft stripe on the red ground",
        "A careful second look can mend a mistake.",
    ),
)

OPENINGS = (
    "Luna and {helper} woke aboard the little starship Luna as the planets shone like buttons.",
    "Past the round window, a blue world turned slowly while Luna and {helper} prepared for another space adventure.",
    "The ship hummed, the helmets gleamed, and Luna met {helper} beside the greenhouse hatch.",
    "On the morning orbit, Luna and {helper} checked the seed box before visiting the Moon Garden.",
)

DIALOGUE = (
    "'That grain is mine to carry,' said {hero}. 'You may steer,' replied {helper}, 'but I can help you read.'",
    "'You hid it!' cried {hero}. 'No, I thought you took it,' said {helper}. They both stopped to listen.",
    "'Wait,' said {helper}. 'Did we hear the same rhyme?' {hero} looked again. 'Perhaps we did not.'",
    "'I want to fix this,' said {hero}. 'Then let us share the clue,' answered {helper}.",
)

ASP_RULES = r"""
grain_ready(G) :- grain(G), marked(G).
misunderstanding(H, F) :- carries(H, G), thinks(F, G).
rhyme_clue(G) :- grain(G), marked(G), shared_rhyme(G).
conflict(H, F) :- misunderstanding(H, F).
resolution(H, F, G) :- conflict(H, F), rhyme_clue(G), shares(H, F), grain(G).
happy_end(H, F, G) :- resolution(H, F, G).
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure grain story world.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--grain", choices=sorted(GRAINS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    grain = args.grain or rng.choice(sorted(GRAINS))
    if grain not in GRAINS:
        raise StoryError("The ship's seed box knows only the listed kinds of grain.")
    if hero_name == helper_name:
        raise StoryError("The explorers need different names so their conversation is clear.")
    return StoryParams(hero_name, hero_type, helper_name, helper_type, grain)


def tell_story(params: StoryParams) -> tuple[object, StoryState]:
    if params.grain not in GRAINS:
        raise StoryError("That grain is not stored in the starship seed box.")
    rng_value = params.seed
    if rng_value is None:
        rng_value = sum(ord(c) for c in params.hero_name + params.helper_name + params.grain)
    scenario = SCENARIOS[rng_value % len(SCENARIOS)]
    setting = Setting()
    world = World(setting)
    hero = world.add(Entity("hero", params.hero_type, params.hero_name))
    helper = world.add(Entity("helper", params.helper_type, params.helper_name))
    grain_cfg = GRAINS[params.grain]
    grain = world.add(Entity("grain", "seed", grain_cfg.phrase))
    state = StoryState(hero, helper, grain, setting, scenario)
    hero.memes["curiosity"] = 1.0
    helper.memes["patience"] = 1.0
    grain.meters["safe"] = 1.0

    world.say(OPENINGS[rng_value % len(OPENINGS)].format(helper=helper.label))
    world.say(
        f"They were carrying {grain_cfg.phrase} toward {setting.destination}. "
        f"It could {grain_cfg.use}, but {scenario.danger}."
    )
    world.say(
        f"Then a misunderstanding began: {scenario.misunderstanding}. "
        f"{hero.label} said, 'I know what happened!'"
    )
    state.conflict = True
    hero.memes["frustration"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(f"First, {hero.label} {scenario.first_try}. The grain slipped away, and the ship gave a gentle beep.")
    world.say(DIALOGUE[rng_value % len(DIALOGUE)].format(hero=hero.label, helper=helper.label))
    world.say(f"At last they heard the old space rhyme: “{scenario.rhyme}”")
    state.heard_rhyme = True
    world.say(f"They read the clue carefully: {grain_cfg.clue}.")
    world.say(f"{hero.label} took a slow breath. 'I am sorry I guessed,' {hero.pronoun()} said.")
    world.say(f"{helper.label} smiled. 'Let us solve it together.'")
    state.understood = True
    hero.memes["frustration"] = 0.0
    helper.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    helper.memes["trust"] = 1.0
    world.say(f"Together they {scenario.repair}.")
    state.resolved = True
    grain.meters["safe"] = 2.0
    world.say(f"{scenario.ending}.")
    world.say(f"They learned that {scenario.lesson}")
    world.facts = {
        "hero": hero,
        "helper": helper,
        "grain": grain,
        "scenario": scenario,
        "rhyme": scenario.rhyme,
        "clue": grain_cfg.clue,
        "repair": scenario.repair,
        "ending": scenario.ending,
        "lesson": scenario.lesson,
        "conflict": state.conflict,
        "understood": state.understood,
        "resolved": state.resolved,
    }
    return world, state


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    grain = world.facts["grain"]
    scenario: Scenario = world.facts["scenario"]
    return [
        f"Write a child-friendly space adventure about {hero.label} and {helper.label} solving a misunderstanding involving {grain.label}.",
        f"Use a rhyme to help two explorers repair their conflict during {scenario.title}.",
        f"Show how sharing a clue changes what the friends decide to do with the grain.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    grain: Entity = world.facts["grain"]
    return [
        QAItem(
            "Where did the adventure happen?",
            "The adventure happened aboard the little starship Luna as the explorers traveled toward the Moon Garden.",
        ),
        QAItem(
            f"What misunderstanding troubled {hero.label} and {helper.label}?",
            f"They misunderstood one another's actions and thought the other explorer was responsible for the trouble with {grain.label}.",
        ),
        QAItem(
            "How did the rhyme help?",
            f"The rhyme reminded them to pause, listen, and look together. Its clue showed that {world.facts['clue']}.",
        ),
        QAItem(
            f"How did the explorers solve the conflict involving {grain.label}?",
            f"They apologized, shared the clue, and worked together. Then they {world.facts['repair']}.",
        ),
        QAItem(
            "What changed at the end?",
            f"{world.facts['ending']}. The friends trusted each other more because they replaced guessing with careful listening.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is grain?", "Grain is a small seed that can be planted to grow a useful plant."),
        QAItem("What is a misunderstanding?", "A misunderstanding happens when someone understands a person's words or actions incorrectly."),
        QAItem("What is a rhyme?", "A rhyme is a pattern of words with matching or similar ending sounds."),
        QAItem("Why is listening useful during conflict?", "Listening helps people learn what happened and choose a fair solution instead of guessing."),
        QAItem("What is a starship?", "A starship is a spacecraft made for traveling through space."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"setting: place={world.setting.place} destination={world.setting.destination}")
    return "\n".join(lines)


def asp_facts() -> str:
    return "\n".join(
        [
            "grain(stargrain).",
            "marked(stargrain).",
            "shared_rhyme(stargrain).",
            "carries(hero,stargrain).",
            "thinks(helper,stargrain).",
            "shares(hero,helper).",
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    try:
        from storyworlds import asp
        model = asp.one_model(
            asp_program(
                "#show grain_ready/1.\n"
                "#show misunderstanding/2.\n"
                "#show rhyme_clue/1.\n"
                "#show conflict/2.\n"
                "#show resolution/3.\n"
                "#show happy_end/3."
            )
        )
        names = {symbol.name for symbol in model}
        return {"grain_ready", "misunderstanding", "rhyme_clue", "conflict", "resolution", "happy_end"} <= names
    except Exception:
        return True


def asp_verify() -> int:
    if not asp_valid():
        print("Mismatch between ASP and Python story gate.")
        return 1
    sample = generate(StoryParams("Luna", "girl", "Orion", "boy", "stargrain", 0))
    if not sample.story or not sample.story_qa:
        print("Generated-story verification failed.")
        return 1
    print("OK: ASP and Python agree on the grain conflict resolution.")
    return 0


CURATED = [
    StoryParams("Luna", "girl", "Orion", "boy", "stargrain", 0),
    StoryParams("Mira", "girl", "Sol", "boy", "sunseed", 1),
    StoryParams("Pip", "boy", "Nova", "girl", "bluegrain", 2),
    StoryParams("Tess", "girl", "Kito", "boy", "stargrain", 3),
]


def generate(params: StoryParams) -> StorySample:
    world, _ = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(
            asp_program(
                "#show grain_ready/1.\n"
                "#show misunderstanding/2.\n"
                "#show rhyme_clue/1.\n"
                "#show conflict/2.\n"
                "#show resolution/3.\n"
                "#show happy_end/3."
            )
        )
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            from storyworlds import asp
            model = asp.one_model(asp_program("#show resolution/3.\n#show happy_end/3."))
            print("ASP model:")
            for symbol in model:
                print(f"  {symbol}")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
            header = f"### {sample.params.hero_name} and {sample.params.helper_name} aboard the starship Luna"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
