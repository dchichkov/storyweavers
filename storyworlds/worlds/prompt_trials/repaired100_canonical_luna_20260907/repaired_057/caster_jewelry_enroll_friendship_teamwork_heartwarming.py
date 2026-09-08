#!/usr/bin/env python3
"""
A heartwarming story world about a young caster, a piece of jewelry, and the
friendship and teamwork needed to enroll a new helper in a caring little team.
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


@dataclass
class Setting:
    place: str = "the little moonlit workshop"
    affordances: set[str] = field(default_factory=lambda: {"practice", "listen", "enroll", "share"})


@dataclass(frozen=True)
class Scenario:
    title: str
    problem: str
    first_try: str
    clue: str
    teamwork: str
    discovery: str
    resolution: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    caster_name: str
    caster_type: str
    friend_name: str
    friend_type: str
    jewelry: str
    seed: Optional[int] = None


@dataclass
class StoryState:
    caster: Entity
    friend: Entity
    jewelry: Entity
    setting: Setting
    enrolled: bool = False
    teamwork: bool = False
    friendship: bool = False
    scenario: Optional[Scenario] = None
    first_try: str = ""
    clue: str = ""
    discovery: str = ""
    resolution: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
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


JEWELRY = {
    "star_pendant": {
        "label": "star pendant",
        "phrase": "a small silver star pendant",
        "quality": "a warm blue gleam",
    },
    "sun_bracelet": {
        "label": "sun bracelet",
        "phrase": "a golden bracelet dotted with tiny suns",
        "quality": "a soft amber glow",
    },
    "moon_brooch": {
        "label": "moon brooch",
        "phrase": "a round moon brooch with a pearl clasp",
        "quality": "a quiet pearly shimmer",
    },
}

CASTER_NAMES = ["Luna", "Mira", "Nell", "Tavi", "Iris", "Pip"]
FRIEND_NAMES = ["Rowan", "Sage", "Wren", "Jo", "Milo", "Penny"]

SCENARIOS = (
    Scenario(
        title="the lantern-circle enrollment",
        problem="the workshop's welcome lantern had gone dim just before a new child arrived",
        first_try="raised the wand and cast a bright spark toward the lantern",
        clue="the spark bounced away whenever the lantern's three little mirrors were not facing one another",
        teamwork="held two mirrors steady while the new child gently turned the third",
        discovery="the jewelry's reflection connected all three mirrors into one shining path",
        resolution="welcomed the new child into the lantern circle and let everyone light one small corner",
        lesson="a kind team makes room for every person's careful hands",
        ending="When evening came, the lantern glowed like a tiny moon, and nobody stood outside its circle",
    ),
    Scenario(
        title="the ribbon-garden enrollment",
        problem="the friendship garden's colored ribbons had tangled, so the newest helper could not find the place to add a green ribbon",
        first_try="cast a sorting spell that lifted every ribbon at once",
        clue="the ribbons only settled when someone named their colors slowly",
        teamwork="unwound one ribbon while the new child matched each color card",
        discovery="the jewelry shone whenever a ribbon reached the right garden post",
        resolution="enrolled the new helper by tying a green ribbon beside the team's friendship tree",
        lesson="teamwork grows when people listen before they rush",
        ending="The garden swayed in the breeze, with one green ribbon dancing beside all the old ones",
    ),
    Scenario(
        title="the lost-lullaby enrollment",
        problem="the workshop choir had forgotten the final note of its welcome lullaby",
        first_try="cast a loud echo into the rafters",
        clue="the missing note was hiding in the quiet space between two voices",
        teamwork="hummed the first line while the new child listened for the place where the ending belonged",
        discovery="the jewelry gave a gentle shimmer when the right note was sung",
        resolution="enrolled the new singer and finished the lullaby together",
        lesson="friendship can begin when someone is invited to share what they hear",
        ending="The last note floated over the tables, and the new singer smiled into the warm hush",
    ),
    Scenario(
        title="the pocket-charm enrollment",
        problem="the team needed one more pocket charm to carry kind wishes to the town's lonely neighbors",
        first_try="cast a charm-making spell all by herself",
        clue="the spell made a shiny shell but no message could fit inside",
        teamwork="measured the little paper, folded it with the new child, and tied it with a soft thread",
        discovery="the jewelry warmed when the message was folded with care",
        resolution="enrolled the new helper as the team's keeper of kind messages",
        lesson="small work becomes special when friends make it together",
        ending="By bedtime, three pocket charms rested in a basket, each holding a bright little wish",
    ),
    Scenario(
        title="the bridge-of-beads enrollment",
        problem="a bead bridge on the workshop noticeboard had lost its middle bead",
        first_try="cast a searching spell that sent beads rolling across the floor",
        clue="the missing bead was still attached to a loose thread beneath the noticeboard",
        teamwork="held the thread while the new child chose the bead's matching color",
        discovery="the jewelry's color showed which side of the bridge needed the bead",
        resolution="repaired the bridge and enrolled the new child as its careful keeper",
        lesson="friends solve more when each person brings a different strength",
        ending="The bead bridge stretched bright across the board, joining every name from end to end",
    ),
)


ASP_RULES = r"""
caster(caster).
jewelry(jewel).
curious(caster).
owns(caster,jewel).
friend(friend).
meets(caster,friend).
shareable(jewel).
teamwork(caster,friend).
can_enroll(caster,friend) :- curious(caster), friend(friend), teamwork(caster,friend).
friendship(caster,friend) :- can_enroll(caster,friend), shareable(jewel).
enrolled(friend) :- friendship(caster,friend).
happy_end(caster,friend) :- enrolled(friend).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming caster and friendship story world.")
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--jewelry", choices=sorted(JEWELRY))
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--friend-gender", choices=["girl", "boy"])
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
    caster_type = args.gender or rng.choice(["girl", "boy"])
    friend_type = args.friend_gender or rng.choice(["girl", "boy"])
    caster_name = args.name or rng.choice(CASTER_NAMES)
    friend_name = args.friend or rng.choice([name for name in FRIEND_NAMES if name != caster_name])
    jewelry = args.jewelry or rng.choice(sorted(JEWELRY))
    if caster_name == friend_name:
        raise StoryError("The caster and friend need different names so their conversation is clear.")
    return StoryParams(
        caster_name=caster_name,
        caster_type=caster_type,
        friend_name=friend_name,
        friend_type=friend_type,
        jewelry=jewelry,
    )


def make_state(world: World, params: StoryParams) -> StoryState:
    caster = world.add(Entity("caster", params.caster_type, params.caster_name))
    friend = world.add(Entity("friend", params.friend_type, params.friend_name))
    jewelry = world.add(Entity("jewel", "jewelry", JEWELRY[params.jewelry]["label"]))
    return StoryState(caster=caster, friend=friend, jewelry=jewelry, setting=world.setting)


def tell_story(params: StoryParams) -> tuple[World, StoryState]:
    world = World(Setting())
    state = make_state(world, params)
    choice = params.seed
    if choice is None:
        choice = sum((index + 1) * ord(char) for index, char in enumerate(params.caster_name + params.friend_name))
    scenario = SCENARIOS[choice % len(SCENARIOS)]
    state.scenario = scenario
    state.first_try = scenario.first_try
    state.clue = scenario.clue

    world.say(
        f"In the little moonlit workshop, {state.caster.label} practiced gentle magic while "
        f"{state.friend.label} sorted ribbons, beads, and buttons."
    )
    world.say(
        f"That morning, {scenario.problem}. {state.caster.label} wore "
        f"{JEWELRY[params.jewelry]['phrase']}, and its {JEWELRY[params.jewelry]['quality']} rested against "
        f"{state.caster.pronoun() if hasattr(state.caster, 'pronoun') else 'their'} coat."
    )
    world.say(
        f"First, {state.caster.label} {scenario.first_try}. But the spell did not help, because {scenario.clue}."
    )
    world.say(
        f"'{state.friend.label}, will you try with me?' asked {state.caster.label}. "
        f"'Yes,' said {state.friend.label}. 'And perhaps we can invite the new helper, too.'"
    )
    world.say(
        f"They worked side by side: {scenario.teamwork}. "
        f"The {state.jewelry.label} twinkled as {scenario.discovery}."
    )

    state.teamwork = True
    state.friendship = True
    state.enrolled = True
    state.caster.memes["friendship"] = 1.0
    state.caster.memes["teamwork"] = 1.0
    state.friend.memes["friendship"] = 1.0
    state.friend.memes["belonging"] = 1.0
    state.jewelry.meters["warmth"] = 1.0
    state.discovery = scenario.discovery
    state.resolution = scenario.resolution

    world.say(
        f"Together they {scenario.resolution}. "
        f"'{state.friend.label}, you belong with us,' said {state.caster.label}. "
        f"'Then I will help someone else belong tomorrow,' {state.friend.label} replied."
    )
    world.say(f"{state.caster.label} learned that {scenario.lesson}.")
    world.say(f"{scenario.ending}.")

    world.facts = {
        "caster": state.caster,
        "friend": state.friend,
        "jewelry": state.jewelry,
        "problem": scenario.problem,
        "first_try": scenario.first_try,
        "clue": scenario.clue,
        "teamwork": scenario.teamwork,
        "discovery": scenario.discovery,
        "resolution": scenario.resolution,
        "lesson": scenario.lesson,
        "ending": scenario.ending,
        "enrolled": state.enrolled,
        "friendship": state.friendship,
        "teamwork_done": state.teamwork,
    }
    return world, state


def generation_prompts(world: World) -> list[str]:
    caster: Entity = world.facts["caster"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    jewelry: Entity = world.facts["jewelry"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about caster {caster.label}, {jewelry.label}, friendship, and teamwork.",
        f"Tell how {caster.label} and {friend.label} use jewelry and teamwork to enroll a new friend.",
        f"Write a gentle workshop tale in which a magical caster discovers that friendship makes room for everyone.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    caster: Entity = world.facts["caster"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    jewelry: Entity = world.facts["jewelry"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did {caster.label} and {friend.label} face?",
            answer=f"They faced a problem because {world.facts['problem']}.",
        ),
        QAItem(
            question=f"What did {caster.label} try first?",
            answer=f"First, {caster.label} {world.facts['first_try']}, but the clue showed that this would not solve the problem.",
        ),
        QAItem(
            question=f"How did teamwork help {caster.label} and {friend.label}?",
            answer=f"They worked together when they {world.facts['teamwork']}. This helped because {world.facts['discovery']}.",
        ),
        QAItem(
            question=f"How did the {jewelry.label} matter?",
            answer=f"The {jewelry.label} mattered because {world.facts['discovery']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"Together they {world.facts['resolution']}. {world.facts['ending']}.",
        ),
    ]


def make_world_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is a caster?",
            answer="A caster is someone who uses magic or a special skill to make something happen.",
        ),
        QAItem(
            question="What is jewelry?",
            answer="Jewelry is a small decorative item, such as a pendant, bracelet, or brooch, that someone can wear.",
        ),
        QAItem(
            question="What does it mean to enroll someone?",
            answer="To enroll someone means to welcome them into a group, class, or team.",
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because people can combine their different strengths to solve a problem together.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world, _state = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=make_world_qa(),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
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
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    return "\n".join(
        [
            "caster(caster).",
            "jewelry(jewel).",
            "curious(caster).",
            "owns(caster,jewel).",
            "friend(friend).",
            "meets(caster,friend).",
            "shareable(jewel).",
            "teamwork(caster,friend).",
        ]
    ) + "\n"


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    try:
        from storyworlds import asp
    except ImportError:
        try:
            import asp
        except ImportError as exc:
            print(f"ASP verification unavailable: {exc}")
            return 1
    program = asp_program(
        "#show can_enroll/2.\n"
        "#show friendship/2.\n"
        "#show enrolled/1.\n"
        "#show happy_end/2."
    )
    symbols = asp.one_model(program)
    names = {symbol.name for symbol in symbols}
    required = {"can_enroll", "friendship", "enrolled", "happy_end"}
    if not required.issubset(names):
        print("Mismatch between ASP and Python gate.")
        return 1
    sample = generate(
        StoryParams(
            caster_name="Luna",
            caster_type="girl",
            friend_name="Rowan",
            friend_type="boy",
            jewelry="star_pendant",
            seed=7,
        )
    )
    if not sample.story or not sample.story_qa:
        print("Generated story verification failed.")
        return 1
    print("OK: ASP and Python agree that teamwork can enroll a friend.")
    return 0


CURATED = [
    StoryParams("Luna", "girl", "Rowan", "boy", "star_pendant", 0),
    StoryParams("Mira", "girl", "Sage", "girl", "sun_bracelet", 1),
    StoryParams("Tavi", "boy", "Wren", "girl", "moon_brooch", 2),
    StoryParams("Iris", "girl", "Milo", "boy", "star_pendant", 3),
    StoryParams("Pip", "boy", "Penny", "girl", "sun_bracelet", 4),
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
        print(
            asp_program(
                "#show can_enroll/2.\n"
                "#show friendship/2.\n"
                "#show enrolled/1.\n"
                "#show happy_end/2."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
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
        header = ""
        if args.all:
            header = f"### {sample.params.caster_name} and {sample.params.friend_name} in the moonlit workshop"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
