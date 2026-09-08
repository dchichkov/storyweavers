#!/usr/bin/env python3
"""A gentle, humorous ghost story about an opposite little haunting."""

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

NAMES = ["Luna", "Milo", "Pip", "Nora", "Theo", "Mabel", "Finn", "Ivy"]
PLACES = ["the old library", "the moonlit inn", "the village clock tower", "the quiet museum"]
GHOST_NAMES = ["Boo", "Wisp", "Misty", "Flicker"]
ROOMS = ["the attic", "the reading room", "the bell chamber", "the dusty hallway"]

OPENINGS = [
    "Moonlight slipped through the crooked windows.",
    "The old building creaked as if it were telling a joke.",
    "A silver fog curled under the front door.",
    "The clock struck eleven, then seemed embarrassed and struck eleven again.",
    "Every candle leaned toward the same mysterious corner.",
]

HUMOR_LINES = [
    "If you are a ghost, please haunt politely.",
    "That is not a frightening moan; it sounds like a hungry goose.",
    "I expected a ghost, but I did not expect one with such terrible timing.",
    "Please stop rattling the windows until I finish counting them.",
    "A proper ghost should at least know where it left its sheet.",
]

GHOST_LINES = [
    "Boo! I am trying to be terrifying.",
    "Do not laugh. My haunting is very important.",
    "I am the opposite of scary tonight.",
    "My spooky plan keeps getting tangled.",
    "Could you help me frighten the right way around?",
]

ENDING_IMAGES = [
    "At dawn, the ghost waved from the chimney while the villagers waved back.",
    "The moon shone on a tidy hallway where one friendly sheet hung like a flag.",
    "From then on, the midnight bell rang once for fear and twice for laughter.",
    "The old building became known as the only haunted place with a welcome mat.",
    "Boo left smiling, and the empty window gave one last cheerful wink.",
]


@dataclass(frozen=True)
class Case:
    key: str
    trouble: str
    opposite: str
    clue: str
    solution: str
    result: str
    lesson: str
    sound: str


CASES = [
    Case(
        "backward_boo",
        "a ghost kept appearing in the mirror before it entered the room",
        "the reflection waved first and looked more surprised than the ghost",
        "the mirror reversed every movement",
        "Luna turned the mirror toward the wall and invited the ghost to practice facing forward",
        "Boo finally entered the room first and gave a proper, if tiny, fright",
        "An opposite result can be a clue, not a catastrophe.",
        "plink",
    ),
    Case(
        "sneezing_shadow",
        "a shadow stretched across the floor whenever the ghost tried to hide",
        "the shadow sneezed loudly and gave away the hiding place",
        "moonlight was shining through a dusty curtain",
        "Luna opened the curtain, shook out the dust outside, and gave the shadow a clean patch of darkness",
        "The ghost hid successfully, though its sneeze still needed work",
        "Achoo!",
    ),
    Case(
        "floating_hat",
        "the ghost's hat floated away whenever it shouted boo",
        "the hat landed on Luna's head instead of frightening her",
        "the hat's feather was caught in a warm chimney draft",
        "Luna closed the draft and pinned the feather with a ribbon",
        "The hat stayed put, but Luna looked so grand that the ghost began laughing",
        "flop",
    ),
    Case(
        "silent_bell",
        "the tower bell refused to ring during the ghost's grand entrance",
        "a tiny mouse rang it from below with one polite tap",
        "the bell rope had slipped behind a crate",
        "Luna moved the crate and tied the rope in a bright loop",
        "The bell rang, and the mouse bowed as if it had planned everything",
        "dong",
    ),
    Case(
        "friendly_footsteps",
        "footsteps followed Luna through the empty hallway",
        "they stopped whenever she turned around and started whenever she walked backward",
        "a loose floorboard creaked only when pressed from one direction",
        "Luna marked the board with chalk and showed the ghost a safer path",
        "The footsteps marched in a neat circle and sounded more like a parade than a warning",
        "creak-creak",
    ),
    Case(
        "upside_down_wail",
        "the ghost's wail came out upside down",
        "instead of a deep moan, it sounded like a squeaky kettle",
        "a loose curtain cord was brushing the ghost's mouth",
        "Luna tied the cord away and asked the ghost to breathe before trying again",
        "Boo made one low wail, then added the kettle sound for the encore",
        "whistle",
    ),
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    room: str


@dataclass
class StoryParams:
    place: str
    room: str
    hero_name: str
    ghost_name: str
    case_key: str
    opening_index: int
    humor_index: int
    ghost_line_index: int
    ending_index: int
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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


def get_case(key: str) -> Case:
    for case in CASES:
        if case.key == key:
            return case
    raise StoryError(f"Unknown ghost case: {key}")


def speak(world: World, name: str, line: str) -> None:
    world.say(f'"{line}" {name} said.')


def tell(setting: Setting, params: StoryParams) -> World:
    case = get_case(params.case_key)
    world = World(setting)
    luna = world.add(Entity("hero", "child", params.hero_name))
    ghost = world.add(Entity("ghost", "ghost", params.ghost_name))
    mirror = world.add(Entity("object", "haunted_object", "the old object"))

    luna.memes.update(curiosity=1.0, courage=1.0, humor=1.0)
    ghost.memes.update(fright=1.0, embarrassment=1.0, relief=0.0)
    mirror.meters.update(safety=1.0, mystery=1.0)
    ghost.holder = None
    ghost.owner = "old_house"

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    humor = HUMOR_LINES[params.humor_index % len(HUMOR_LINES)]
    ghost_line = GHOST_LINES[params.ghost_line_index % len(GHOST_LINES)]
    ending = ENDING_IMAGES[params.ending_index % len(ENDING_IMAGES)]

    world.say(opening)
    world.say(
        f"In {setting.place}, {params.hero_name} entered {setting.room} carrying a small lantern. "
        f"Everyone said the place was haunted by {params.ghost_name}, but nobody agreed on what "
        "the ghost was supposed to do."
    )
    world.para()

    speak(world, params.ghost_name, ghost_line)
    world.say(f"{case.sound.upper()}! {case.trouble.capitalize()}.")
    world.say(f"But the opposite happened: {case.opposite.capitalize()}.")
    speak(world, params.hero_name, humor)
    world.para()

    world.say(
        f"{params.hero_name} did not run. Instead, {params.hero_name} looked closely and noticed that {case.clue}."
    )
    speak(world, params.hero_name, "Let us solve the strange part before we blame the ghost.")
    speak(world, params.ghost_name, "I can help, although I am better at drifting than thinking.")
    world.say(
        f"Together they {case.solution}. The ghost watched carefully, because a clue was more useful "
        "than a loud scream."
    )
    world.para()

    world.say(case.result + ".")
    world.say(
        f"{params.hero_name} learned that {case.lesson} "
        f"{params.ghost_name} learned that a haunting works best when everyone understands the plan."
    )
    world.say(ending)

    luna.meters.update(courage=1.0, investigated=1.0, helped=1.0)
    ghost.meters.update(practiced=1.0, safe=1.0, laughed=1.0)
    ghost.memes["relief"] = 1.0
    world.fired.update(
        {
            ("appearance", "ghost"),
            ("opposite", case.key),
            ("clue", case.key),
            ("resolution", case.key),
        }
    )
    world.facts.update(
        hero=luna,
        ghost=ghost,
        object=mirror,
        case=case,
        opening=opening,
        humor=humor,
        ghost_line=ghost_line,
        ending=ending,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        f"Write a humorous ghost story about {params.hero_name} meeting {params.ghost_name} in {params.room}.",
        f"Use an opposite surprise: {case.opposite}. Let a concrete clue guide the solution.",
        "End with a friendly image showing that courage and laughter changed the haunting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {params.hero_name} meet {params.ghost_name}?",
            f"{params.hero_name} met {params.ghost_name} in {params.room} at {params.place}.",
        ),
        QAItem(
            "What was opposite about the haunting?",
            f"The opposite surprise was that {case.opposite}.",
        ),
        QAItem(
            "What clue explained the strange event?",
            f"The clue was that {case.clue}.",
        ),
        QAItem(
            "How did the child and ghost solve the problem?",
            f"They solved it when they {case.solution}.",
        ),
        QAItem(
            "What changed by the end?",
            f"{case.result}. The ghost became safer and more cheerful, while the child understood that {case.lesson.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a ghost story?",
            "A ghost story is an imaginary tale about a spirit or haunting, often with mystery and suspense.",
        ),
        QAItem(
            "What does opposite mean?",
            "Opposite means very different or reversed from something else, such as quiet compared with loud.",
        ),
        QAItem(
            "Why can humor help during a frightening moment?",
            "Humor can make a frightening moment feel smaller and can help people think clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
    lines.append(f"events={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
haunting(G,H) :- ghost(G), hero(H), enters(H,house).
opposite(G,H) :- haunting(G,H), strange_event(G).
clue(H,G) :- opposite(G,H), observes(H).
humor(H,G) :- clue(H,G), speaks(H).
safe(H,G) :- humor(H,G), repairs(H,G).
resolution(H,G) :- safe(H,G).
#show haunting/2.
#show opposite/2.
#show clue/2.
#show humor/2.
#show safe/2.
#show resolution/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("ghost", "ghost"),
            asp.fact("hero", "hero"),
            asp.fact("enters", "hero", "house"),
            asp.fact("strange_event", "ghost"),
            asp.fact("observes", "hero"),
            asp.fact("speaks", "hero"),
            asp.fact("repairs", "hero", "ghost"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    required = {"haunting", "opposite", "clue", "humor", "safe", "resolution"}
    found = {name for name in required if asp.atoms(model, name)}
    if found != required:
        raise StoryError(f"ASP parity failed: expected {required}, found {found}")
    for case in CASES:
        sample = generate(
            StoryParams(
                place=PLACES[0],
                room=ROOMS[0],
                hero_name="Luna",
                ghost_name="Boo",
                case_key=case.key,
                opening_index=0,
                humor_index=0,
                ghost_line_index=0,
                ending_index=0,
            )
        )
        if "opposite" not in sample.story.lower() and "opposite" not in sample.story_qa[1].answer.lower():
            raise StoryError("Generated story lost the seed concept.")
        if len(sample.story.split()) < 80:
            raise StoryError("Generated story is too short.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous opposite ghost-story world.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--room", choices=ROOMS)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--ghost", choices=GHOST_NAMES)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        room=args.room or rng.choice(ROOMS),
        hero_name=args.name or rng.choice(NAMES),
        ghost_name=args.ghost or rng.choice(GHOST_NAMES),
        case_key=rng.choice(CASES).key,
        opening_index=rng.randrange(len(OPENINGS)),
        humor_index=rng.randrange(len(HUMOR_LINES)),
        ghost_line_index=rng.randrange(len(GHOST_LINES)),
        ending_index=rng.randrange(len(ENDING_IMAGES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(params.place, params.room), params)
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


CURATED = [
    StoryParams("the old library", "the reading room", "Luna", "Boo", "backward_boo", 0, 0, 0, 0),
    StoryParams("the village clock tower", "the bell chamber", "Milo", "Wisp", "silent_bell", 1, 2, 1, 2),
    StoryParams("the moonlit inn", "the attic", "Nora", "Misty", "floating_hat", 2, 3, 2, 3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
