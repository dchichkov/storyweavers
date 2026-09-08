#!/usr/bin/env python3
"""
A gentle bedtime story world about a quiet galley, a hidden surprise, and the
joy of learning by asking questions.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
STORYWORLDS_ROOT = next(
    (parent for parent in HERE.parents if (parent / "results.py").is_file()),
    HERE.parent,
)
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Location:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str
    friend_name: str
    keeper_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    opening: str
    vessel: str
    mystery: str
    foreshadowing: str
    discovery: str
    lesson: str
    ending: str
    bedtime_image: str


TALES = [
    Tale(
        opening="Moonlight rested on the little harbor while everyone in the old galley prepared supper.",
        vessel="a blue kettle that hummed whenever someone asked a brave question",
        mystery="the galley lantern had gone dark, and nobody could remember where its star-shaped wick was kept",
        foreshadowing="a tiny silver glimmer winked beneath the flour basket",
        discovery="the wick was tucked inside a seashell used as a measuring cup",
        lesson="questions can turn ignorance into a path toward understanding",
        ending="the lantern shone across the water, and every sleepy boat seemed to smile",
        bedtime_image="the moon laid a silver road from the galley door to the quiet sea",
    ),
    Tale(
        opening="On a calm evening, the galley smelled of cinnamon, warm bread, and rain on the roof.",
        vessel="a copper soup pot that sang one soft note before each surprise",
        mystery="the final spoonful of honey for the night cakes had vanished",
        foreshadowing="three golden crumbs curved toward the old spice cupboard",
        discovery="the honey jar had rolled behind a bundle of lavender",
        lesson="not knowing is a beginning, not a reason to feel ashamed",
        ending="the cakes rose sweetly, and the whole crew shared them beneath the stars",
        bedtime_image="lavender shadows danced while warm cake cooled on the wooden table",
    ),
    Tale(
        opening="The sleepy lighthouse galley rocked gently as the evening tide whispered below.",
        vessel="a brass bell that chimed whenever a new idea was spoken aloud",
        mystery="the keeper could not find the little map needed to guide a lost gull home",
        foreshadowing="a feather trembled beside the folded napkins",
        discovery="the map rested inside the bell's padded travel box",
        lesson="curiosity can stimulate careful thinking and kind action",
        ending="the gull found its way home, and the keeper gave everyone a bright feather badge",
        bedtime_image="the lighthouse beam swept softly over the waves like a giant lullaby",
    ),
    Tale(
        opening="Far from the busy shore, a tiny galley floated beneath a sky full of sleepy stars.",
        vessel="a wooden rolling pin that wiggled whenever a secret was nearby",
        mystery="the cook's recipe for moon-shaped biscuits had lost its last line",
        foreshadowing="a dusting of flour marked a trail beneath the captain's chair",
        discovery="the missing line was written on the back of a little tide chart",
        lesson="asking for help makes a puzzling world feel friendlier",
        ending="the biscuits came out perfectly round, and even the shyest sailor took one",
        bedtime_image="floury stars covered the table while the galley settled into silence",
    ),
    Tale(
        opening="At bedtime, the harbor galley glowed with one warm window and the sound of gentle spoons.",
        vessel="a green bowl that grew brighter whenever someone admitted what they did not know",
        mystery="the crew could not tell which tiny seed would grow into the night garden's first flower",
        foreshadowing="a soft green thread curled from a crack near the pantry",
        discovery="the seed had already sprouted in a cup of rainwater",
        lesson="ignorance can become wonder when we observe patiently",
        ending="the first flower opened before dawn, pink as a sleepy cheek",
        bedtime_image="the new flower nodded beside the galley window as everyone drifted to sleep",
    ),
]

CHILD_NAMES = ["Luna", "Mira", "Pip", "Nell", "Toby"]
FRIEND_NAMES = ["Bram", "Ivy", "Oren", "Suki", "Wren"]
KEEPER_NAMES = ["Mara", "Nia", "Sol", "Tess", "Ari"]

ASP_RULES = r"""
#show uncertain/1.
#show learns/1.
#show resolves/1.

questioning :- child(luna).
questioning :- child(mira).
questioning :- child(pip).
questioning :- child(nell).
questioning :- child(toby).

uncertain(galley) :- mystery(galley).
learns(galley) :- questioning, clue(galley).
resolves(galley) :- learns(galley), helper(galley).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime galley story about curiosity.")
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--keeper-name", choices=KEEPER_NAMES)
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
    child = args.child_name or rng.choice(CHILD_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name != child]
    friend = args.friend_name or rng.choice(friend_choices)
    keeper = args.keeper_name or rng.choice(KEEPER_NAMES)
    if friend == child:
        raise StoryError("The child and friend must have different names.")
    return StoryParams(
        child_name=child,
        friend_name=friend,
        keeper_name=keeper,
    )


class World:
    def __init__(self, params: StoryParams) -> None:
        self.location = Location(
            name="the moonlit galley",
            meters={"distance_to_shore": 18.0, "lantern_light": 0.0},
            memes={"calm": 0.6, "curiosity": 0.2, "belonging": 0.4},
        )
        self.entities: dict[str, Character] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.dialogue_turns: list[tuple[str, str]] = []
        self._add(Character("child", params.child_name, "child"))
        self._add(Character("friend", params.friend_name, "friend"))
        self._add(Character("keeper", params.keeper_name, "galley keeper"))

    def _add(self, entity: Character) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def speak(self, speaker: str, words: str) -> None:
        self.dialogue_turns.append((speaker, words))
        self.say(f'{speaker} said, "{words}"')

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def _variation_index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(char) for char in params.child_name + params.friend_name + params.keeper_name)


def _setup(params: StoryParams) -> World:
    world = World(params)
    world.facts["params"] = params
    return world


def generate_story(world: World, params: StoryParams) -> None:
    child = world.entities["child"]
    friend = world.entities["friend"]
    keeper = world.entities["keeper"]
    index = _variation_index(params)
    tale = TALES[index % len(TALES)]

    world.facts.update(
        tale=tale,
        child=child.name,
        friend=friend.name,
        keeper=keeper.name,
        tale_index=index % len(TALES),
        mystery_open=True,
        learned=False,
        resolved=False,
    )

    world.say(tale.opening)
    world.say(
        f"{child.name} and {friend.name} were helping {keeper.name} in the galley, "
        f"where {tale.vessel} waited beside the stove."
    )
    world.say(
        f"Then {tale.mystery.capitalize()}. The grown-ups searched, but the answer stayed "
        "hidden in the dim corners."
    )

    world.para()
    world.speak(child.name, "I do not know where it is, but may I ask some questions?")
    world.speak(keeper.name, "Of course. Wonder is a good lamp when a room feels dark.")
    world.say(
        f"{child.name} looked carefully instead of pretending to understand everything. "
        f"{tale.foreshadowing.capitalize()}."
    )
    world.speak(friend.name, "I saw that glimmer too. Shall we follow it gently?")
    world.speak(child.name, "Yes. We can learn one small thing at a time.")

    child.memes["curiosity"] = 0.9
    friend.memes["cooperation"] = 0.9
    keeper.memes["trust"] = 0.9
    world.location.memes["curiosity"] = 0.9

    world.para()
    world.say(
        f"They lifted the basket, followed the glimmer, and discovered that {tale.discovery}."
    )
    world.facts["mystery_open"] = False
    world.facts["learned"] = True
    world.location.meters["lantern_light"] = 1.0
    world.location.memes["belonging"] = 0.95
    world.say(
        f"The surprise made everyone laugh softly. The thing they had not known was no longer "
        f"a wall; it was a new bit of knowledge. {tale.lesson.capitalize()}."
    )
    world.speak(keeper.name, "You did not need to know everything before you began.")
    world.speak(child.name, "I only needed to notice, ask, and keep going.")
    world.facts["resolved"] = True

    world.para()
    world.say(f"{tale.ending}.")
    world.say(f"As the galley grew quiet, {tale.bedtime_image}.")
    world.say("And with curious hearts warm and safe, the friends fell asleep.")


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    keeper = world.facts["keeper"]
    return [
        QAItem(
            question=f"Where were {child} and {friend}, and who was with them?",
            answer=(
                f"{child} and {friend} were in the moonlit galley with {keeper}, "
                "the galley keeper."
            ),
        ),
        QAItem(
            question="What problem began the story?",
            answer=f"The problem was that {tale.mystery}.",
        ),
        QAItem(
            question="What clue foreshadowed the surprise?",
            answer=f"The clue was that {tale.foreshadowing}.",
        ),
        QAItem(
            question="How did asking questions change the story?",
            answer=(
                f"{child} admitted not knowing, asked questions, and looked carefully with "
                f"{friend}. Together they discovered that {tale.discovery}, so the mystery "
                "became a happy piece of knowledge."
            ),
        ),
        QAItem(
            question="What peaceful image ended the bedtime story?",
            answer=f"The ending image was that {tale.bedtime_image}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a galley?",
            answer="A galley is a kitchen on a ship or boat where people prepare food.",
        ),
        QAItem(
            question="What does ignorance mean?",
            answer="Ignorance means not knowing or not yet understanding something.",
        ),
        QAItem(
            question="How can questions stimulate learning?",
            answer=(
                "Questions stimulate learning by directing attention, inviting observation, "
                "and helping people find information they did not know before."
            ),
        ),
        QAItem(
            question="Why is it kind to admit that you do not know something?",
            answer=(
                "Admitting that you do not know makes it easier to ask for help, investigate "
                "carefully, and learn without pretending."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]
    return [
        (
            f"Write a gentle bedtime story about {world.facts['child']} in a galley, where "
            f"{tale.mystery}. Include a kind dialogue exchange."
        ),
        (
            f"Tell a story in which ignorance becomes curiosity: use the foreshadowing "
            f"that {tale.foreshadowing}, then reveal that {tale.discovery}."
        ),
        (
            f"Create a happy ending for a moonlit galley tale. Show how questions stimulate "
            f"learning and finish with {tale.bedtime_image}."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: name={entity.name} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"  {world.location.name}: meters={world.location.meters} "
        f"memes={world.location.memes}"
    )
    lines.append(f"  mystery_open={world.facts.get('mystery_open')}")
    lines.append(f"  learned={world.facts.get('learned')}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  dialogue turns={len(world.dialogue_turns)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _setup(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child", "luna"),
            asp.fact("mystery", "galley"),
            asp.fact("clue", "galley"),
            asp.fact("helper", "galley"),
        ]
    )


def asp_program(show: str = "#show uncertain/1.\n#show learns/1.\n#show resolves/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


CURATED = [
    StoryParams("Luna", "Bram", "Mara", seed=11),
    StoryParams("Mira", "Ivy", "Nia", seed=12),
    StoryParams("Pip", "Oren", "Sol", seed=13),
    StoryParams("Nell", "Suki", "Tess", seed=14),
    StoryParams("Toby", "Wren", "Ari", seed=15),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    uncertain = asp.atoms(model, "uncertain")
    learns = asp.atoms(model, "learns")
    resolves = asp.atoms(model, "resolves")
    if ("galley",) not in uncertain:
        print("MISMATCH: ASP did not mark the galley as uncertain.")
        return 1
    if ("galley",) not in learns:
        print("MISMATCH: ASP did not derive learning.")
        return 1
    if ("galley",) not in resolves:
        print("MISMATCH: ASP did not derive resolution.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if len(sample.world.dialogue_turns) < 4:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
    print("OK: ASP and Python agree, and generated stories resolve with dialogue.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("uncertain:", asp.atoms(model, "uncertain"))
        print("learns:", asp.atoms(model, "learns"))
        print("resolves:", asp.atoms(model, "resolves"))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        for offset in range(args.n):
            rng = random.Random(base_seed + offset)
            params = resolve_params(args, rng)
            params.seed = base_seed + offset
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
