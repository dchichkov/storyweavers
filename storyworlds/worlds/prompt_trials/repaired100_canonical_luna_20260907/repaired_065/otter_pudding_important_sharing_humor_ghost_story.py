#!/usr/bin/env python3
"""A child-friendly ghost story about an otter, pudding, and important sharing."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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

NAMES = ["Luna", "Milo", "Pip", "Nora", "Otis", "Mabel"]
PLACES = ["the moonlit boathouse", "the old riverside kitchen", "the misty harbor cottage", "the quiet reed hut"]
HELPERS = ["Grandma", "Aunt Bea", "Uncle Sam", "Mr. Reed"]
OTTERS = ["Pebble", "Willow", "Scoop", "Moss"]

OPENINGS = [
    "The moon hung over the river like a silver button.",
    "Fog curled around the little boathouse after supper.",
    "A cold breeze tapped the kitchen window three times.",
    "The reeds whispered while the last daylight faded.",
    "The river shone darkly beneath a sky full of stars.",
]

DIALOGUE = [
    ("Is that pudding for one?", "No. Important treats are for sharing."),
    ("Did the ghost take the spoon?", "Perhaps it only wanted a taste."),
    ("Should we hide the bowl?", "Let us share it before the pudding disappears."),
    ("Are you frightened?", "Only of a pudding ghost with an empty tummy."),
    ("Who is knocking?", "A hungry friend, I think."),
]

HAUNTS = [
    "a pale spoon floated above the bowl",
    "a wet footprint appeared beside the pudding",
    "the cupboard door opened with a tiny sigh",
    "a translucent tail curled around the table leg",
    "three ghostly chuckles rose from the empty pantry",
]

CLUES = [
    "a silver paw print led from the river door to the dessert table",
    "the spoon was cold, but its handle smelled of sweet cinnamon",
    "the ghostly tail ended in a neat little otter paw",
    "a puddle beside the bowl held tiny whisker marks",
    "the knocking matched the sound of an otter tapping a shell",
]

ENDING_IMAGES = [
    "The ghost faded into moonlight, and the otter licked the last pudding from its whiskers.",
    "By midnight, the bowl was empty, the spoon was still, and Pebble slept beside the warm stove.",
    "The pale tail waved goodbye before sinking into the river mist.",
    "Everyone laughed as the pudding ghost became only a friendly otter in a sheet of fog.",
    "The moon watched over a clean bowl and two happy friends sharing the final spoonful.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def title(self) -> str:
        return self.label


@dataclass(frozen=True)
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper: str
    otter_name: str
    seed: Optional[int] = None
    opening_index: int = 0
    dialogue_index: int = 0
    haunt_index: int = 0
    clue_index: int = 0
    ending_index: int = 0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


def speak(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.title()} said.')


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.hero_name, "child"))
    helper = world.add(Entity("helper", "character", params.helper, "adult"))
    otter = world.add(Entity("otter", "animal", params.otter_name, "otter"))
    pudding = world.add(
        Entity(
            "pudding",
            "food",
            "the pudding",
            "dessert",
            meters={"fullness": 1.0, "shared": 0.0},
            memes={"importance": 1.0, "comfort": 1.0},
        )
    )
    ghost = world.add(Entity("ghost", "spirit", "the pudding ghost", "ghost"))

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    question, answer = DIALOGUE[params.dialogue_index % len(DIALOGUE)]
    haunt = HAUNTS[params.haunt_index % len(HAUNTS)]
    clue = CLUES[params.clue_index % len(CLUES)]
    ending = ENDING_IMAGES[params.ending_index % len(ENDING_IMAGES)]

    world.say(opening)
    world.say(
        f"In {setting.place}, {hero.title()} carried a warm bowl of pudding to the table. "
        f"The pudding was important because {helper.title()} had made it to celebrate a kind day."
    )
    world.say(
        f"Outside, {otter.title()} the otter pressed his nose to the window. "
        "He had followed the smell from the river, but he was too shy to knock."
    )
    world.para()

    speak(world, hero, question)
    speak(world, helper, answer)
    world.say(
        f"Just then, {haunt}. A chilly giggle slid under the door, and the bowl trembled."
    )
    world.say(f"{hero.title()} looked at the shadow on the wall. It had two round ears and a very silly tail.")
    world.para()

    world.say(f"The shadow whispered, 'Share, share, or pudding will vanish!' Then {clue}.")
    speak(world, hero, "Are you a ghost, or are you simply hungry?")
    speak(world, otter, "Both, perhaps. I am hungry enough to haunt a spoon.")
    world.say(
        f"The otter had spoken, and his whiskers wobbled so hard that {hero.title()} laughed. "
        "The frightening shadow was only moonlight shining through a wet curtain."
    )
    world.para()

    world.say(
        f"{hero.title()} placed the bowl in the middle of the table. "
        f"{helper.title()} gave {otter.title()} a small spoon, and everyone took one fair turn."
    )
    pudding.meters["shared"] = 1.0
    pudding.meters["fullness"] = 0.0
    otter.memes.update(comfort=1.0, trust=1.0, humor=1.0)
    hero.memes.update(kindness=1.0, courage=1.0, sharing=1.0)
    helper.memes.update(guidance=1.0, sharing=1.0)
    ghost.memes.update(humor=1.0, harmless=1.0)
    world.fired.update({"haunt", "clue", "dialogue", "sharing", "resolution"})
    world.say(
        f"With every shared spoonful, the ghostly chill grew warmer. "
        f"At last, {ending}"
    )
    world.say(
        "Everyone agreed that an important treat tastes better when nobody has to eat it alone."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        otter=otter,
        pudding=pudding,
        ghost=ghost,
        haunt=haunt,
        clue=clue,
        ending=ending,
        question=question,
        answer=answer,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a humorous ghost story about {params.hero_name}, an otter, and important pudding.",
        f"Tell a child-friendly tale set in {params.place} where sharing solves a spooky problem.",
        "Make the ghost seem frightening at first, then reveal a warm and funny reason for the haunting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    otter: Entity = world.facts["otter"]  # type: ignore[assignment]
    pudding: Entity = world.facts["pudding"]  # type: ignore[assignment]
    clue = str(world.facts["clue"])
    ending = str(world.facts["ending"])

    return [
        QAItem(
            question=f"Why was the pudding important to {hero.title()}?",
            answer=(
                f"{helper.title()} had made the pudding to celebrate a kind day, "
                "so it was a special treat rather than an ordinary snack."
            ),
        ),
        QAItem(
            question=f"What made the pudding seem haunted?",
            answer=(
                f"The children saw {world.facts['haunt']}, heard a chilly giggle, "
                "and noticed a strange shadow near the bowl."
            ),
        ),
        QAItem(
            question="What clue explained the spooky shadow?",
            answer=(
                f"They noticed that {clue}. "
                "The clue showed that the shadow came from moonlight, water, and the hungry otter."
            ),
        ),
        QAItem(
            question=f"What did {otter.title()} say when the children asked who he was?",
            answer=(
                f"{otter.title()} joked, 'Both, perhaps. I am hungry enough to haunt a spoon.' "
                "His silly answer made everyone laugh."
            ),
        ),
        QAItem(
            question="How did sharing change the evening?",
            answer=(
                f"The bowl was placed in the middle, and everyone took a fair turn. "
                "The otter felt welcome, the spooky chill faded, and the pudding became a happy shared memory."
            ),
        ),
        QAItem(
            question="What final image showed that the problem was solved?",
            answer=f"{ending} This showed that the frightening haunting had become a friendly supper.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is sharing important?",
            answer="Sharing is important because it lets others enjoy something too and helps people feel included.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something that makes people smile or laugh, often by turning a surprise into a playful joke.",
        ),
        QAItem(
            question="What should someone do when a spooky event seems confusing?",
            answer="They should stay calm, look for clues, and ask a trusted person what may be happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        bits = [f"type={entity.type}"]
        if entity.owner:
            bits.append(f"owner={entity.owner}")
        if entity.holder:
            bits.append(f"holder={entity.holder}")
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {entity.title()} {' '.join(bits)}")
    lines.append(f"events: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
haunted(P,G) :- pudding(P), ghost(G), not shared(P).
hungry(O,P) :- otter(O), pudding(P), not shared(P).
invite(H,O,P) :- hero(H), otter(O), pudding(P), haunted(P,G).
shared(P) :- pudding(P), kind_act(P).
kind_act(P) :- pudding(P), invited(P).
safe(P) :- shared(P), pudding(P).
#show haunted/2.
#show hungry/2.
#show invite/3.
#show shared/1.
#show safe/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("otter", "otter"),
            asp.fact("pudding", "pudding"),
            asp.fact("ghost", "ghost"),
            asp.fact("invited", "pudding"),
            asp.fact("kind_act", "pudding"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_parity() -> set[str]:
    import asp

    model = asp.one_model(asp_program())
    return {
        f"{name}{args}"
        for name in ("haunted", "hungry", "invite", "shared", "safe")
        for args in asp.atoms(model, name)
    }


def python_parity() -> set[str]:
    return {
        "haunted('pudding','ghost')",
        "hungry('otter','pudding')",
        "invite('hero','otter','pudding')",
        "shared('pudding')",
        "safe('pudding')",
    }


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
        if asp_parity() != python_parity():
            print("ASP/Python parity failed", file=sys.stderr)
            return 1
    except ImportError:
        print("clingo is required for --verify", file=sys.stderr)
        return 1

    for i in range(10):
        params = resolve_params(build_parser().parse_args([]), random.Random(i))
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous ghost story about sharing pudding with an otter.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--otter", choices=OTTERS)
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
        hero_name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        otter_name=args.otter or rng.choice(OTTERS),
        opening_index=rng.randrange(len(OPENINGS)),
        dialogue_index=rng.randrange(len(DIALOGUE)),
        haunt_index=rng.randrange(len(HAUNTS)),
        clue_index=rng.randrange(len(CLUES)),
        ending_index=rng.randrange(len(ENDING_IMAGES)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero_name not in NAMES:
        raise StoryError(f"Unknown hero name: {params.hero_name}")
    world = tell(Setting(params.place), params)
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
    StoryParams(
        place="the moonlit boathouse",
        hero_name="Luna",
        helper="Grandma",
        otter_name="Pebble",
        opening_index=0,
        dialogue_index=0,
        haunt_index=1,
        clue_index=0,
        ending_index=0,
    ),
    StoryParams(
        place="the old riverside kitchen",
        hero_name="Milo",
        helper="Aunt Bea",
        otter_name="Willow",
        opening_index=2,
        dialogue_index=3,
        haunt_index=3,
        clue_index=2,
        ending_index=3,
    ),
    StoryParams(
        place="the misty harbor cottage",
        hero_name="Nora",
        helper="Uncle Sam",
        otter_name="Scoop",
        opening_index=4,
        dialogue_index=1,
        haunt_index=4,
        clue_index=4,
        ending_index=4,
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
