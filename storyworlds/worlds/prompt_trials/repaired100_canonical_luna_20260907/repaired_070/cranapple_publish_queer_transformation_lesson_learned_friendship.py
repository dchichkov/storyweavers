#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a cranapple, a brave queer transformation,
a small act of publishing, and the friendship that grows around it.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "moonlit_garden": "the moonlit garden",
    "quiet_attic": "the quiet attic",
    "lantern_library": "the lantern library",
}

NAMES = ["Luna", "Mira", "Sol", "Robin", "Tavi", "Aster"]
FRIEND_NAMES = ["Pip", "Nell", "Jun", "Clover", "Sage", "Wren"]
MOODS = ["hopeful", "thoughtful", "curious", "gentle", "brave"]
COLORS = ["silver", "violet", "golden", "blue", "rose"]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("whole", "open", "shared", "published", "changed"):
            self.meters.setdefault(key, 0.0)
        for key in ("hope", "worry", "belonging", "friendship", "confidence", "curiosity"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    name: str
    friend: str
    mood: str
    color: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    title: str
    beginning: str
    worry: str
    first_try: str
    clue: str
    dialogue: str
    plan: str
    transformation: str
    lesson: str
    ending: str


TALES = [
    Tale(
        "The Cranapple Moon",
        "Luna found a round cranapple glowing beneath the moonflower vines",
        "she wondered whether a fruit that was part cranberry and part apple could belong anywhere",
        "she hid it in a basket and tried to make it look like an ordinary apple",
        "a little silver moth landed on the fruit, as if it had found exactly the right home",
        '"Maybe it does not need to choose only one name," Pip said',
        "write the cranapple story honestly, then publish it on the garden notice tree",
        "the cranapple became a bright emblem of welcome, and Luna began to stand more proudly in her own changing shape",
        "A queer transformation can be beautiful when we stop treating difference as a mistake",
        "the published page fluttered beside the moonflowers while Luna and Pip shared the first sweet slice",
    ),
    Tale(
        "The Little Book with Two Covers",
        "Mira discovered a cranapple beside the old printing press in the attic",
        "the press could print only one cover, and Mira feared her unusual story would be too queer for anyone to read",
        "she tried to squeeze two different beginnings into one cramped line",
        "the blank back page was wide enough for a second color and a second voice",
        '"What if the book can grow instead of shrinking?" Mira asked',
        "make a book with two welcoming covers, read it together, and publish it for anyone who needed a gentle surprise",
        "the little book changed from a private worry into a shared doorway",
        "A lesson learned through friendship can turn a strange beginning into a place to enter",
        "the book rested under a lantern, its two covers open like friendly wings",
    ),
    Tale(
        "The Orchard Name",
        "Sol carried a cranapple from the orchard to a quiet table near the library window",
        "the fruit had changed colors overnight, and Sol worried that changing might mean being lost",
        "Sol covered the fruit with a cloth and waited for it to become simple again",
        "the orchard keeper explained that roots can stay connected while new branches grow",
        '"You are still you while you become more yourself," Wren said',
        "draw the changing cranapple, write down what it taught them, and publish the page in the library",
        "Sol let the changing colors show, and confidence replaced the wish to hide",
        "Transformation does not erase a true self; it can reveal more of it",
        "the published drawing glowed in the window as the cranapple wore all its colors",
    ),
    Tale(
        "The Night Garden Notice",
        "Robin and Clover found a cranapple beside a blank notice in the lantern library",
        "Robin wanted to publish a queer little poem, but worried that nobody would understand it",
        "Robin tore up the first poem after one sleepy doubt",
        "Clover noticed that the poem made the lantern flame burn steadier",
        '"I understand the feeling, even before I understand every word," Clover said',
        "keep the poem, add a clear title, and publish it beside the reading cushion",
        "the poem changed from a hidden scrap into a small light for other readers",
        "Friendship listens for the heart of a story and helps it find its readers",
        "by bedtime, three quiet children had read the poem and left warm stars beside it",
    ),
]


OPENINGS = [
    "On a soft evening",
    "Just before bedtime",
    "Under a sky full of sleepy stars",
    "When the last teacup had been washed",
    "As the moon climbed above the rooftops",
]

TURN_LEADS = [
    "The peaceful evening grew difficult when",
    "A small worry appeared when",
    "The trouble began softly:",
    "For a while, the lovely discovery felt heavy because",
]

CLUE_LEADS = [
    "Then a nearby detail offered a kinder idea.",
    "A patient look revealed something important.",
    "The night seemed to whisper a clue.",
    "Instead of hiding the problem, they examined it together.",
]

ENDING_LEADS = [
    "At last",
    "When the lamps grew low",
    "Before everyone went to sleep",
    "By the final silver hour",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


def choose_tale(params: StoryParams) -> tuple[Tale, str, str, str, str]:
    rng = random.Random(params.seed)
    return (
        rng.choice(TALES),
        rng.choice(OPENINGS),
        rng.choice(TURN_LEADS),
        rng.choice(CLUE_LEADS),
        rng.choice(ENDING_LEADS),
    )


def propagate(world: World) -> None:
    child = world.get("child")
    friend = world.get("friend")
    fruit = world.get("cranapple")
    page = world.get("page")

    if page.meters["shared"] >= 1 and "friendship" not in world.fired:
        world.fired.add("friendship")
        child.memes["friendship"] += 1
        friend.memes["friendship"] += 1
        child.memes["belonging"] += 1
        friend.memes["belonging"] += 1

    if fruit.meters["changed"] >= 1 and "confidence" not in world.fired:
        world.fired.add("confidence")
        child.memes["confidence"] += 1
        child.memes["worry"] = 0.0

    if page.meters["published"] >= 1 and "published" not in world.fired:
        world.fired.add("published")
        page.meters["open"] = 1.0
        child.memes["hope"] += 1
        friend.memes["hope"] += 1


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")
    if params.color not in COLORS:
        raise StoryError(f"Unknown color: {params.color}")

    world = World(Setting(params.place))
    child = world.add(Entity("child", "character", "child", params.name))
    friend = world.add(Entity("friend", "character", "friend", params.friend))
    fruit = world.add(Entity("cranapple", "food", "fruit", "cranapple", owner=params.name))
    page = world.add(Entity("page", "thing", "page", "a story page"))
    child.memes["curiosity"] = 1
    child.memes["worry"] = 1
    friend.memes["curiosity"] = 1
    fruit.meters["whole"] = 1
    page.meters["open"] = 1

    tale, opening, turn_lead, clue_lead, ending_lead = choose_tale(params)
    values = {
        "child": params.name,
        "friend": params.friend,
        "place": params.place,
        "color": params.color,
    }
    fill = lambda text: text.format(**values)

    story: list[str] = []
    story.append(
        f"{opening}, {params.name}, who felt {params.mood}, visited {params.place} with {params.friend}."
    )
    story.append(f"There they found a cranapple: {fill(tale.beginning)}.")
    story.append(
        f"It was {params.color} on one side and rosy on the other, and it seemed to carry a quiet secret."
    )
    story.append(f"{turn_lead} {fill(tale.worry)}.")
    story.append(f"{params.name}'s first try was to {fill(tale.first_try)}.")
    story.append(f"{clue_leads := clue_lead} {fill(tale.clue)}.")
    story.append(fill(tale.dialogue) + ".")
    story.append(f"{params.name} listened. Then {params.friend} listened too.")
    story.append(f"Together they decided to {fill(tale.plan)}.")

    page.meters["shared"] = 1
    fruit.meters["changed"] = 1
    page.meters["published"] = 1
    propagate(world)

    story.append(f"{params.name} wrote carefully, and {params.friend} held the lantern steady.")
    story.append(f"Their queer little project changed: {fill(tale.transformation)}.")
    story.append(fill(tale.lesson) + ".")
    story.append(f"{ending_lead}, {fill(tale.ending)}.")

    world.facts.update(
        tale=tale,
        story=story,
        child=child,
        friend=friend,
        cranapple=fruit,
        page=page,
        published=True,
        transformed=True,
    )
    return world


def render(world: World) -> str:
    return " ".join(world.facts["story"])


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        "Write a gentle bedtime story involving a cranapple, a queer transformation, publishing, a lesson learned, and friendship.",
        f"Tell a bedtime tale about {child.label} and {friend.label} discovering a cranapple and choosing to publish its unusual story.",
        f"Write a child-facing story in which friendship helps {child.label} understand that transformation can reveal belonging.",
        f"Use this story turn: {tale.dialogue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.label} and {friend.label} discover?",
            answer=f"They discovered a cranapple and realized that {tale.beginning.lower()}.",
        ),
        QAItem(
            question="What worry caused the problem?",
            answer=f"The worry was that {tale.worry}.",
        ),
        QAItem(
            question="How did the friends respond?",
            answer=f"They listened to one another and decided to {tale.plan}.",
        ),
        QAItem(
            question="What transformation took place?",
            answer=f"Their queer project changed because {tale.transformation}.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=tale.lesson + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cranapple?",
            answer="A cranapple is an imaginary fruit with qualities of both a cranberry and an apple.",
        ),
        QAItem(
            question="What does publish mean?",
            answer="To publish means to share writing or art so that other people can read or see it.",
        ),
        QAItem(
            question="What can queer mean?",
            answer="Queer can be a welcoming word for identities or ways of being that do not fit narrow expectations.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change from one state or shape into another.",
        ),
        QAItem(
            question="Why is friendship useful?",
            answer="Friendship can offer listening, care, courage, and a sense that nobody has to face a worry alone.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id:10} ({entity.type:8}) meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
shared(page) :- page(page).
transformed(cranapple) :- cranapple(cranapple), shared(page).
published(page) :- page(page), shared(page).
good_story :- published(page), transformed(cranapple), friendship.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "storyworld"),
            asp.fact("page", "page"),
            asp.fact("cranapple", "cranapple"),
            asp.fact("friendship"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        symbols = asp.one_model(asp_program())
        if not any(str(symbol) == "good_story" for symbol in symbols):
            raise StoryError("ASP did not derive good_story")
    except ImportError:
        return 0
    print("OK: ASP and Python agree that the published transformation is a good story.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedtime storyworld about a cranapple, publishing, queer transformation, and friendship."
    )
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--color", choices=COLORS)
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
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        mood=args.mood or rng.choice(MOODS),
        color=args.color or rng.choice(COLORS),
    )


CURATED = [
    StoryParams("moonlit_garden", "Luna", "Pip", "hopeful", "silver", 1),
    StoryParams("quiet_attic", "Mira", "Nell", "thoughtful", "violet", 2),
    StoryParams("lantern_library", "Sol", "Wren", "brave", "golden", 3),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=render(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        try:
            import asp
            symbols = asp.one_model(asp_program())
            if not any(str(symbol) == "good_story" for symbol in symbols):
                raise StoryError("ASP reasonableness check failed")
        except ImportError:
            pass

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        params = sample.params
        header = ""
        if args.all:
            header = f"### {params.name}: {params.place}"
        elif len(samples) > 1:
            header = f"### bedtime variation {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
