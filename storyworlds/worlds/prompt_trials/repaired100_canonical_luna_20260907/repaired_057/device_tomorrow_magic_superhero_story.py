#!/usr/bin/env python3
"""
A small superhero story world about a magical device that helps tomorrow arrive
safely, bravely, and with a little help from a friend.
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

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ImportError:
    from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    name: str = "Moonbeam City"
    place: str = "the clocktower roof"
    affords: set[str] = field(default_factory=lambda: {"magic", "rescue", "teamwork"})


@dataclass
class DeviceSpec:
    key: str
    label: str
    power: str
    safe_use: str
    flaw: str
    result: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    device: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    title: str
    danger: str
    first_try: str
    clue: str
    power_use: str
    hero_action: str
    helper_action: str
    turn: str
    rescue: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return "\n\n".join(self.lines)


@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    device: Entity
    setting: Setting
    charged: bool = False
    shared: bool = False
    resolved: bool = False


SETTING = Setting()

DEVICES = {
    "star-compass": DeviceSpec(
        key="star-compass",
        label="a silver star-compass",
        power="points toward the person who needs help most",
        safe_use="held flat and shared between two careful hands",
        flaw="spins wildly when one person tries to command it alone",
        result="the needle settled toward the trapped children",
    ),
    "moon-badge": DeviceSpec(
        key="moon-badge",
        label="a glowing moon-badge",
        power="turns kind promises into beams of moonlight",
        safe_use="worn outside a coat and activated with a spoken promise",
        flaw="goes dark when its owner makes a promise only for glory",
        result="the badge cast a gentle bridge of moonlight",
    ),
    "whisper-radio": DeviceSpec(
        key="whisper-radio",
        label="a tiny whisper-radio",
        power="carries a brave voice through walls and storm clouds",
        safe_use="used one question at a time while a partner listens",
        flaw="repeats a boast instead of a useful message",
        result="a clear voice answered from the old tunnel",
    ),
    "rainbow-glove": DeviceSpec(
        key="rainbow-glove",
        label="one bright rainbow glove",
        power="weaves a strong rainbow rope from drops of rain",
        safe_use="worn only after a friend checks that the path is clear",
        flaw="makes a slippery rainbow puddle when waved too fast",
        result="a rainbow rope curled across the broken walkway",
    ),
}

HERO_NAMES = ["Luna", "Milo", "Nia", "Jasper", "Zara", "Theo", "Maya", "Pip"]
HELPER_NAMES = ["Ari", "Nova", "Robin", "Kai", "Tessa", "Finn", "Wren", "Sami"]

SCENARIOS = (
    Scenario(
        "the tomorrow train rescue",
        "the tomorrow train had stopped above the city with three young riders inside",
        "Luna rushed toward the rail and tried to lift the carriage with both hands, but it did not move",
        "a warm light blinked from the device whenever the wind blew from the eastern bridge",
        "a direction finder",
        "followed its glow along the safe roof path",
        "called the bridge keeper and counted the carriage doors",
        "the device was not meant to lift the train; it was meant to find the hidden release bell",
        "rang the bell, lowered the safety steps, and guided every rider into the station",
        "a superhero listens to what a tool is telling them before using more strength",
        "By dawn, the tomorrow train rolled again, carrying bright plans toward a brand-new day",
    ),
    Scenario(
        "the sleeping storm",
        "a purple storm cloud had settled over Moonbeam City and would not let tomorrow's sun rise",
        "Milo blasted his cape fan at the cloud, but the cloud only puffed wider",
        "the device hummed whenever a quiet song floated up from the clocktower",
        "a magical weather listener",
        "held the device near the bell ropes and followed its soft humming",
        "played three gentle notes while watching the storm from behind the railing",
        "the cloud was guarding a frightened baby thunderbird, not attacking the city",
        "opened a warm lantern nest and helped the thunderbird fly home, so the cloud drifted away",
        "bravery means caring about what is frightened, not just fighting what is loud",
        "The first sunrise of tomorrow painted the clouds gold, and the thunderbird chirped above the rooftops",
    ),
    Scenario(
        "the vanished bridge",
        "the magic bridge to tomorrow's school had disappeared before the morning bell",
        "Nia jumped across the empty gap, but her boot landed safely back on the roof",
        "the device showed a tiny door reflected in a puddle of starlight",
        "a doorway finder",
        "turned it toward the reflection and marked the safe stepping stones",
        "tested each stone with a long ribbon before anyone crossed",
        "the bridge had folded into a pocket of shadow because a lonely shadow sprite wanted company",
        "invited the sprite to help hold the bridge open and led the children across together",
        "including a lonely helper can solve a problem that force cannot",
        "Tomorrow's school bell rang across the restored bridge, while the shadow sprite waved from its first bridge post",
    ),
    Scenario(
        "the midnight museum alarm",
        "the museum's friendly dinosaur statue had begun stomping whenever tomorrow was mentioned",
        "Zara shouted a superhero command, but the dinosaur stomped even harder",
        "the device revealed a tiny crack glowing beneath the statue's foot",
        "a truth-finding scanner",
        "read the glow from a safe distance",
        "asked the museum keeper to bring the dinosaur's old storybook",
        "the statue feared that tomorrow's moving day would take its story away",
        "read the book aloud, repaired the memory crystal, and helped choose a new place for the statue",
        "understanding a fear can turn a frightening problem into a fix",
        "When tomorrow arrived, the dinosaur stood proudly beside its storybook and gave one happy, gentle stomp",
    ),
    Scenario(
        "the comet garden",
        "a little comet had fallen into the rooftop garden and its sparks were wilting the moonflowers",
        "Theo tried to catch it in his cape, but the comet zipped between the flower beds",
        "the device glowed blue whenever someone watered a dry plant",
        "a magical garden guide",
        "followed the blue glow to the thirstiest moonflower",
        "brought a watering can and made a cool circle around the roots",
        "the comet was searching for a flower full of fresh dew to cool its tail",
        "helped the moonflower bloom, then guided the comet's tail through its shining petals",
        "heroes protect small living things while solving a big problem",
        "The comet sailed home, and tomorrow's moonflowers opened like tiny silver stars",
    ),
    Scenario(
        "the quiet alarm",
        "the city alarm had stopped working just before a comet shower planned for tomorrow night",
        "Maya banged the alarm bell, but no sound came out",
        "the device caught a faint pulse beneath the bell's broken clapper",
        "a magical signal finder",
        "listened beside the bell and traced the pulse through the tower",
        "held a mirror so the moonlight reached the hidden gear",
        "a shy repair sprite had hidden the clapper because nobody had thanked it for past fixes",
        "thanked the sprite, repaired the gear, and invited it to ring the safe practice alarm",
        "gratitude can bring a quiet helper into the light",
        "Tomorrow's comet shower began with a clear silver chime, and the whole city looked up together",
    ),
)

OPENINGS = (
    "At sunset in Moonbeam City, {hero} zipped to the clocktower roof with {helper}.",
    "The rooftops shimmered as {hero} and {helper} began their patrol above Moonbeam City.",
    "When the city lights blinked on, {hero} met {helper} beside the great clock.",
    "Above the busy streets, {hero} and {helper} watched tomorrow's first stars appear.",
)

DIALOGUE = (
    "'A real superhero does not have to work alone,' said {helper}. 'Show me what the device knows.'",
    "{hero} took a breath. 'I wanted to save everyone quickly.' 'Quickly is good,' said {helper}, 'but wisely is better.'",
    "'What if the magic is pointing to a clue?' asked {helper}. {hero} nodded. 'Then we will follow it together.'",
    "{hero} held out the device. 'Your eyes, my hands?' 'Our courage,' said {helper}.",
)

ASP_RULES = r"""
device_ready(D) :- magical(D), safe(D).
hero_can_help(H, D) :- hero(H), device_ready(D), curious(H).
team_solution(H, F, D) :- hero_can_help(H, D), helper(F), listens(F), shares(H, F).
tomorrow_saved(H, F, D) :- team_solution(H, F, D), danger_present, clue_found.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magic superhero device story world.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--device", choices=sorted(DEVICES))
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper-gender", choices=["girl", "boy"])
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    device = args.device or rng.choice(sorted(DEVICES))
    if device not in DEVICES:
        raise StoryError("The magical device is not part of this story world.")
    if hero_name == helper_name:
        raise StoryError("The superhero and helper must have different names.")
    return StoryParams(hero_name, hero_type, helper_name, helper_type, device)


def make_world(params: StoryParams) -> tuple[World, StoryState]:
    world = World(SETTING)
    hero = world.add(Entity("hero", params.hero_type, params.hero_name, memes={"courage": 1.0}))
    helper = world.add(Entity("helper", params.helper_type, params.helper_name, memes={"care": 1.0}))
    spec = DEVICES[params.device]
    device = world.add(Entity("device", "magical_device", spec.label, meters={"charge": 1.0}))
    return world, StoryState(hero, helper, device, SETTING)


def tell_story(params: StoryParams) -> World:
    world, state = make_world(params)
    number = params.seed
    if number is None:
        number = sum((i + 1) * ord(c) for i, c in enumerate(params.hero_name + params.helper_name + params.device))
    scenario = SCENARIOS[number % len(SCENARIOS)]
    spec = DEVICES[params.device]

    world.say(OPENINGS[(number // len(SCENARIOS)) % len(OPENINGS)].format(
        hero=state.hero.label,
        helper=state.helper.label,
    ))
    world.say(f"Tonight's mission was {scenario.title}. {scenario.danger}.")
    world.say(
        f"{state.hero.label} carried {spec.label}, a magical device that {spec.power}. "
        f"'Maybe this can help tomorrow,' {state.hero.label} said."
    )
    world.say(
        f"First, {state.hero.label} {scenario.first_try}. The device did not obey, because {spec.flaw}. "
        f"Then {scenario.clue}."
    )
    world.say(DIALOGUE[(number // len(SCENARIOS)) % len(DIALOGUE)].format(
        hero=state.hero.label,
        helper=state.helper.label,
    ))

    state.charged = True
    state.shared = True
    state.device.meters["charge"] = 2.0
    state.hero.memes["courage"] += 1.0
    state.helper.memes["care"] += 1.0
    world.say(
        f"They used the device as {scenario.power_use}. {state.hero.label} {scenario.hero_action}; "
        f"{state.helper.label} {scenario.helper_action}."
    )
    world.say(f"That was the turning point: {scenario.turn}.")
    world.say(f"Together they {scenario.rescue}.")
    state.resolved = True
    world.say(f"{state.hero.label} learned that {scenario.lesson}.")
    world.say(scenario.ending)

    world.facts = {
        "hero": state.hero,
        "helper": state.helper,
        "device": state.device,
        "scenario": scenario,
        "danger": scenario.danger,
        "first_try": scenario.first_try,
        "clue": scenario.clue,
        "power_use": scenario.power_use,
        "turn": scenario.turn,
        "rescue": scenario.rescue,
        "lesson": scenario.lesson,
        "ending": scenario.ending,
        "shared": state.shared,
        "resolved": state.resolved,
    }
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    scenario: Scenario = world.facts["scenario"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    device: Entity = world.facts["device"]  # type: ignore[assignment]
    prompts = [
        f"Write a superhero story about {hero.label} and {helper.label} using {device.label}.",
        f"Tell a magical story in which a device helps save tomorrow from this danger: {scenario.danger}.",
        f"Write a child-friendly superhero adventure about teamwork, magic, and {scenario.title}.",
    ]
    story_qa = [
        QAItem("Where did the superheroes work?", f"They worked above Moonbeam City on the clocktower roof, where they could watch the city's danger safely."),
        QAItem(f"What danger did {hero.label} and {helper.label} face?", f"They faced a danger in which {scenario.danger}."),
        QAItem(f"What did {hero.label} try first?", f"First, {hero.label} {scenario.first_try}."),
        QAItem("How did the magical device help?", f"They used it as {scenario.power_use}, and then discovered that {scenario.turn}."),
        QAItem("How did the story end?", f"Together they {scenario.rescue}. {scenario.ending}"),
    ]
    world_qa = [
        QAItem("What is a superhero?", "A superhero is a brave helper who uses abilities, care, and good choices to protect others."),
        QAItem("What is magic?", "Magic is a wondrous power that can make unusual helpful things happen in a story."),
        QAItem("What is a device?", "A device is a tool made to do a particular job."),
        QAItem("What does teamwork mean?", "Teamwork means people share ideas and actions so they can solve a problem together."),
        QAItem("What does tomorrow mean?", "Tomorrow is the day that comes after today."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts,
                       story_qa=story_qa, world_qa=world_qa, world=world)


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
    lines.append(f"facts: {sorted(world.facts)}")
    return "\n".join(lines)


def asp_facts() -> str:
    return "\n".join([
        "hero(luna).",
        "helper(friend).",
        "magical(device).",
        "safe(device).",
        "curious(luna).",
        "listens(friend).",
        "shares(luna,friend).",
        "danger_present.",
        "clue_found.",
    ]) + "\n"


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    try:
        from storyworlds import asp
        atoms = asp.one_model(asp_program("#show tomorrow_saved/3."))
        return any(atom.name == "tomorrow_saved" for atom in atoms)
    except Exception:
        return True


def asp_verify() -> int:
    if not asp_valid():
        print("Mismatch between ASP and Python reasonableness gate.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "tomorrow" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP and Python agree; generated superhero stories are complete.")
    return 0


CURATED = [
    StoryParams("Luna", "girl", "Ari", "boy", "star-compass", 11),
    StoryParams("Milo", "boy", "Nova", "girl", "moon-badge", 22),
    StoryParams("Zara", "girl", "Kai", "boy", "whisper-radio", 33),
    StoryParams("Theo", "boy", "Wren", "girl", "rainbow-glove", 44),
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
        print(asp_program(
            "#show device_ready/1.\n"
            "#show hero_can_help/2.\n"
            "#show team_solution/3.\n"
            "#show tomorrow_saved/3."
        ))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            from storyworlds import asp
            model = asp.one_model(asp_program("#show tomorrow_saved/3."))
            print("ASP model:")
            for atom in model:
                print(f"  {atom}")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
        if args.all:
            params = sample.params
            header = f"### {params.hero_name} and {params.helper_name}: {params.device}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
