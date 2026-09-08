#!/usr/bin/env python3
"""
A child-facing mystery about a friendship mechanism, a warning, and a surprising turn.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the clockwork greenhouse"
    hero: str = "Luna"
    friend: str = "Pip"
    keeper: str = "the quiet caretaker"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the clockwork greenhouse": {
        "tags": {"mechanism", "mystery", "garden"},
        "mood": "hushed and silver",
    },
    "the lantern museum": {
        "tags": {"mechanism", "mystery", "light"},
        "mood": "dim and watchful",
    },
    "the old ferry station": {
        "tags": {"mechanism", "mystery", "water"},
        "mood": "misty and echoing",
    },
}


@dataclass(frozen=True)
class MysteryCase:
    title: str
    premise: str
    clue: str
    danger: str
    dialogue: str
    action: str
    twist: str
    resolution: str
    ending: str
    clue_answer: str
    danger_answer: str
    twist_answer: str
    resolution_answer: str


CASES = [
    MysteryCase(
        "The Bell That Counted Backward",
        "Every midnight, a brass bell in the greenhouse rang one fewer time, and nobody knew who had wound it.",
        "Luna noticed tiny oil marks leading from the bell to a locked seed cabinet.",
        "Pip wanted to open the cabinet at once, but a red thread across its keyhole warned that the gears inside could snap.",
        "\"We should look before we touch,\" said Luna. \"And we should look together,\" Pip replied.",
        "They followed the oil marks with a mirror, seeing a hidden lever behind the cabinet without putting a hand near the gears.",
        "The bell was not counting down to an explosion; it was counting the empty flowerpots that needed water.",
        "They pulled the lever carefully, and a gentle stream filled every dry pot before the last bell note faded.",
        "By morning, green shoots formed a crooked row shaped like two friends holding hands.",
        "The oil marks led from the bell to the locked seed cabinet, where a hidden lever waited.",
        "The cabinet's red thread warned that opening it carelessly could make its gears snap.",
        "The backward count measured empty flowerpots, not a coming explosion.",
        "The friends used the hidden lever carefully, sending water to every dry pot.",
    ),
    MysteryCase(
        "The Vanishing Footprints",
        "Wet footprints appeared across the museum floor each night, then vanished before dawn.",
        "Luna found that every print stopped beneath a display case holding a broken silver key.",
        "A loose pulley above the case creaked whenever someone stepped close, so rushing underneath it was unsafe.",
        "\"I can crawl under it,\" said Pip. \"Not alone,\" said Luna. \"We solve mysteries side by side.\"",
        "They tied a ribbon to a long broom and gently tested the pulley from beyond its falling path.",
        "The footprints belonged to the museum's cleaning machine, which had been following the key's scent, not a ghost.",
        "The key fit the machine's quieting lock, and the frightened night guard learned why the floor kept getting wet.",
        "At sunrise, the last footprint held a tiny reflection of both friends in its puddle.",
        "The prints stopped below the case containing a broken silver key.",
        "The loose pulley could fall if they hurried beneath it.",
        "A cleaning machine made the footprints while searching for the key's scent.",
        "The silver key quieted the machine and explained the wet trail.",
    ),
    MysteryCase(
        "The Clockwork Feather",
        "A golden feather moved from room to room inside the old ferry station, though no bird lived there.",
        "Pip discovered a line of blue chalk beside each place where the feather had rested.",
        "The final chalk mark pointed toward a turning wheel that could catch a sleeve or finger.",
        "\"Let us mark the safe distance,\" said Luna. \"Then we can ask what the feather is showing us,\" said Pip.",
        "They used a stick to turn the wheel from behind a railing and revealed a narrow passage.",
        "The feather was not stolen treasure; it was a signal from a rescue mechanism hidden in the wall.",
        "They reset the mechanism, and a warm lamp lit the station's long-forgotten waiting room.",
        "The golden feather rested above the lamp, glowing like a small sunrise beside their joined shadows.",
        "Blue chalk marked every place where the feather had rested.",
        "The turning wheel could catch a sleeve or finger if approached carelessly.",
        "The feather signaled a hidden rescue mechanism rather than stolen treasure.",
        "Resetting the mechanism lit the forgotten waiting room.",
    ),
    MysteryCase(
        "The Locked Garden Door",
        "A garden door locked itself whenever two people tried to enter, although one person could open it easily.",
        "Luna found three carved stars on the latch and a fourth star scratched beneath the floor mat.",
        "The easiest answer was to force the door, but the old hinges groaned as if they might collapse.",
        "\"Maybe the lock wants a pattern,\" said Pip. \"Maybe it wants us to listen,\" Luna answered.",
        "They tapped the stars in the rhythm of the hinges, then waited together instead of pulling.",
        "The door had been designed to keep out lonely thieves, not to keep out friends.",
        "It opened only when both friends placed their hands on the latch and promised to leave the garden unharmed.",
        "Inside, two small lamps brightened at once, though nobody had lit them.",
        "Three stars were carved on the latch, and a fourth was hidden beneath the mat.",
        "Forcing the door risked collapsing its old hinges.",
        "The lock protected the garden from lonely thieves and welcomed trustworthy friends.",
        "The rhythm and shared promise opened the door safely.",
    ),
    MysteryCase(
        "The Whispering Gear",
        "A gear whispered one word every evening, but its tiny voice was hidden under the sound of rain.",
        "Pip placed a cup beside it and heard the word clearly: \"behind.\"",
        "Behind the gear was a narrow maintenance hatch with a spring that could leap loose if opened quickly.",
        "\"I heard a warning,\" said Pip. \"Then we will treat it like one,\" said Luna.",
        "They held the hatch with a cloth, released the spring slowly, and found a dusty message tube.",
        "The whisper was not a secret command; it was the gear reminding them that its maker had hidden a map behind it.",
        "The map showed a safe path through the flooded station, leading stranded travelers to dry ground.",
        "The gear went quiet after the map was carried outside, as if it had finally finished its sentence.",
        "A cup made the gear's word clear: \"behind.\"",
        "The hatch spring could leap loose if opened quickly.",
        "The gear's whisper directed them to a hidden map, not a secret command.",
        "The map led stranded travelers along a safe path to dry ground.",
    ),
]


OPENINGS = [
    "On a misty afternoon, {hero} and {friend} entered {setting}, where every small mechanism seemed to be holding its breath.",
    "The mystery began when {hero} and {friend} heard a click inside {setting}, followed by a silence too careful to be ordinary.",
    "People said {setting} kept old secrets. {hero} and {friend} came to inspect one, carrying only a notebook, a ribbon, and their trust.",
    "At the edge of {setting}, {hero} found a brass mark shaped like a question. {friend} bent close, and together they followed it inside.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.keeper))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    case: MysteryCase = f["case"]
    opening = _fill(OPENINGS[f["opening_variant"]], f)
    premise = _fill(case.premise, f)
    clue = _fill(case.clue, f)
    danger = _fill(case.danger, f)
    dialogue = _fill(case.dialogue, f)
    action = _fill(case.action, f)
    twist = _fill(case.twist, f)
    resolution = _fill(case.resolution, f)
    ending = _fill(case.ending, f)
    hero = f["hero"]
    friend = f["friend"]
    keeper = f["keeper"]

    structures = [
        [
            f"{opening} The case was called \"{case.title}.\"",
            f"{premise} {clue}",
            f"{keeper.capitalize()} watched from the doorway. {danger}",
            dialogue,
            action,
            f"{twist} {resolution}",
            f"When the mystery was over, {ending}.",
        ],
        [
            opening,
            f"\"What do you notice?\" asked {friend}. {premise}",
            _cap(clue),
            f"{keeper.capitalize()} gave them one caution: {danger[0].lower() + danger[1:]}",
            dialogue,
            f"They tested the mechanism from a safe distance. {action}",
            f"The answer surprised them. {twist} {resolution}",
            f"At last, {ending}.",
        ],
        [
            f"The old report for \"{case.title}\" begins with this image: {ending}.",
            f"Before that ending, {opening.lower()}",
            f"The first clue was simple. {premise} Then {clue[0].lower() + clue[1:]}",
            f"\"We can be brave without being careless,\" said {hero}. {dialogue}",
            action,
            f"The hidden truth was stranger than either friend expected: {twist}",
            resolution,
        ],
        [
            opening,
            f"Something had changed in {setting}. {premise}",
            f"{friend} pointed to the clue. {_cap(clue)}",
            f"{keeper.capitalize()} warned, \"Do not hurry.\" {danger}",
            f"{hero} said, \"We will decide together.\" {dialogue}",
            action,
            f"Then came the twist: {twist}",
            f"{resolution} The proof was clear when {ending}.",
        ],
        [
            f"{opening} Neither friend knew that the mechanism had been waiting for them.",
            f"At first, {premise[0].lower() + premise[1:]}",
            f"They found the clue, but also a risk: {danger[0].lower() + danger[1:]}",
            dialogue,
            f"They made a plan, checked it twice, and then {action[0].lower() + action[1:]}",
            f"The mystery turned on one small surprise. {twist}",
            f"Because they stayed careful and kind, {resolution}",
            f"That night, {ending}.",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
setting(clockwork_greenhouse).
setting(lantern_museum).
setting(old_ferry_station).

feature(mechanism).
feature(friendship).
feature(cautionary).
feature(twist).
style(mystery).

safe_case(S) :- setting(S), feature(mechanism), feature(friendship),
                 feature(cautionary), feature(twist), style(mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    for feature in ("mechanism", "friendship", "cautionary", "twist"):
        lines.append(asp.fact("feature", feature))
    lines.append(asp.fact("style", "mystery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery story world about mechanisms, friendship, caution, and twists."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--keeper")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Milo", "Nia", "Tess", "Rowan"])
    friend = args.friend or rng.choice(["Pip", "Jo", "Mara", "Sol", "Kit"])
    keeper = args.keeper or rng.choice(
        ["the quiet caretaker", "the museum guide", "the station keeper"]
    )
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    if not hero.strip() or not friend.strip():
        raise StoryError("Hero and friend names cannot be empty.")
    return StoryParams(setting=setting, hero=hero, friend=friend, keeper=keeper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}.")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")

    seed = _stable_seed(params)
    case = CASES[seed % len(CASES)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="child detective",
            meters={"curiosity": 0.8, "caution": 0.7},
            memes={"friendship": 1.0},
        )
    )
    friend = world.add(
        Entity(
            name=params.friend,
            kind="child detective",
            meters={"curiosity": 0.8, "caution": 0.7},
            memes={"friendship": 1.0},
        )
    )
    keeper = world.add(
        Entity(
            name=params.keeper,
            kind="caretaker",
            meters={"knowledge": 0.8},
            memes={"caution": 1.0},
        )
    )
    mechanism = world.add(
        Entity(
            name="the hidden mechanism",
            kind="mechanism",
            meters={"movement": 0.4, "risk": 0.5},
            memes={"mystery": 1.0},
        )
    )
    world.add(
        Entity(
            name="the warning clue",
            kind="clue",
            meters={"visibility": 0.7},
            memes={"caution": 1.0},
        )
    )

    world.facts.update(
        hero=hero.name,
        friend=friend.name,
        keeper=keeper.name,
        setting=params.setting,
        case=case,
        opening_variant=(seed // len(CASES)) % len(OPENINGS),
        structure_variant=(seed // (len(CASES) * len(OPENINGS))) % 5,
        title=case.title,
        clue=case.clue,
        danger=case.danger,
        twist=case.twist,
        resolution=case.resolution,
        ending=case.ending,
        theme="mechanism, friendship, caution, and a mystery twist",
    )

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a child-facing mystery about {params.hero} and {params.friend} investigating a mechanism in {params.setting}.",
        "Tell a cautionary friendship mystery in which a careful choice reveals a surprising twist.",
        "Write a gentle mystery where a clue changes what two friends decide to do.",
    ]
    story_qa = [
        QAItem(
            question=f"What was the first important clue in \"{case.title}\"?",
            answer=case.clue_answer,
        ),
        QAItem(
            question="Why did the friends need to be cautious?",
            answer=case.danger_answer,
        ),
        QAItem(
            question="What surprising twist did the friends discover?",
            answer=case.twist_answer,
        ),
        QAItem(
            question=f"How did {params.hero} and {params.friend} resolve the mystery?",
            answer=case.resolution_answer,
        ),
        QAItem(
            question="What final image proves that the mystery changed the setting?",
            answer=f"The story ends with {case.ending}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of moving parts that works together to do something.",
        ),
        QAItem(
            question="Why is caution useful in a mystery?",
            answer="Caution helps people investigate safely instead of touching a dangerous object too quickly.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a detail that helps someone understand or solve a mystery.",
        ),
        QAItem(
            question="How can friendship help during a difficult investigation?",
            answer="Friends can share observations, check one another's choices, and stay brave without taking needless risks.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising change in what a story seems to mean.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
    if qa:
        print()
        print("== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(
        setting.replace("the ", "").replace(" ", "_") for setting in SETTING_REGISTRY
    )


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_case/1."))
    return sorted(set(asp.atoms(model, "safe_case")))


def asp_verify() -> int:
    expected = {(setting,) for setting in _valid_python()}
    actual = set(_asp_valid())
    if expected != actual:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1

    rng = random.Random(17)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1

    print(f"OK: clingo gate matches python ({len(expected)} settings), and stories generate.")
    return 0


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    if args.n < 1:
        raise StoryError("The number of stories must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Luna",
                        friend="Pip",
                        keeper="the quiet caretaker",
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(100, args.n * 100):
            seed = base_seed + index
            index += 1
            rng = random.Random(seed)
            params = build_story_params(args, rng)
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
