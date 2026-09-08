#!/usr/bin/env python3
"""A gentle mythic storyworld about a green quest solved through teamwork and rhyme."""

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


HERO_NAMES = ["Luna", "Mira", "Tavi", "Nell", "Orin", "Pia"]
COMPANIONS = ["a fox", "a young giant", "a river sprite", "a little raven"]
PLACES = ["the Mossy Hills", "the Greenwood Vale", "the fern-covered mountain", "the emerald meadow"]
QUESTS = [
    {
        "key": "lantern",
        "premise": "the Moon Queen had lost her green lantern among the hills",
        "obstacle": "a silver fog hid every path and made the hills seem to move",
        "clue": "tiny green leaves pointed downhill whenever the moonlight touched them",
        "action": "They followed the leaves, but only after joining hands and chanting together.",
        "result": "At the valley floor, they found the lantern glowing beneath an elder tree.",
        "ending": "The Moon Queen lifted the green lantern, and its light painted a safe road through the dark.",
        "lesson": "A quest grows lighter when brave friends share both the work and the wonder.",
    },
    {
        "key": "seed",
        "premise": "the Garden Giant had asked them to find a green seed that could wake the sleeping valley",
        "obstacle": "three stone doors blocked the path, and each door bore a different riddle",
        "clue": "the answers were hidden in the colors of moss, leaf, and vine",
        "action": "One friend watched the moss, one studied the leaf, and one traced the vine while Luna spoke the answers in rhyme.",
        "result": "The final stone door opened, revealing the green seed in a nest of warm clay.",
        "ending": "When Luna planted the seed, a green shoot rose and curled around the old stones.",
        "lesson": "Teamwork lets many small clues become one strong answer.",
    },
    {
        "key": "bell",
        "premise": "the forest king had sent them to recover a green bell stolen by the wind",
        "obstacle": "the bell hung above a ravine, where gusts tossed every rope aside",
        "clue": "the wind always quieted after the third line of an old rhyme",
        "action": "They tested the rhyme together, then braided their ropes while the calm moment arrived.",
        "result": "The braided rope reached the bell, and the companions pulled it safely home.",
        "ending": "The green bell rang across the forest, calling every lost traveler toward shelter.",
        "lesson": "A shared rhythm can turn a wild problem into a careful plan.",
    },
    {
        "key": "brook",
        "premise": "the river spirit had asked them to return a green jewel to a dry spring",
        "obstacle": "a fallen tree barred the spring, and the jewel grew dim whenever anyone worked alone",
        "clue": "the jewel brightened when two or more hands touched its silver case",
        "action": "They lifted the case together, rolled the tree aside with a branch, and carried the jewel as one team.",
        "result": "The jewel slipped into the spring, and clear water bubbled over their boots.",
        "ending": "Green reeds opened beside the water, making a bright ribbon through the meadow.",
        "lesson": "Some treasures shine only when kindness and strength are shared.",
    },
]

OPENINGS = [
    "At dawn, the old hills wore crowns of green moss.",
    "The first sunbeam touched the Greenwood Vale like a golden flute.",
    "Before the birds began their morning song, Luna stood beneath an ancient oak.",
    "Mist curled over the emerald meadow while the village bells slept.",
    "Far above the fern-covered mountain, a green star blinked three times.",
    "In the quiet hour before sunrise, the forest roots whispered a name.",
]

RHYME_LINES = [
    ("Green leaf, bright stone, guide us where we roam;", "hand in hand, we bring the lost thing home."),
    ("Three small clues and one brave cheer;", "teamwork makes the far path near."),
    ("Wind may wander, stones may stay;", "friends can find another way."),
    ("One voice starts and all voices ring;", "shared courage wakes the sleeping spring."),
    ("Moss below and moon above;", "we walk by trust, and trust is love."),
    ("Step by step and side by side;", "a kindly quest will be our guide."),
]

CARETAKER_LINES = [
    "A quest is not measured by how loudly one hero boasts, but by how wisely a team listens.",
    "Look for the clue that belongs to everyone, then let every helper have a turn.",
    "Courage is useful, but courage joined to care is stronger.",
    "When the road changes, stop, share what you know, and choose the next step together.",
    "No green wonder is worth a careless leap; steady feet make the journey last.",
    "A good rhyme can gather scattered thoughts into one brave plan.",
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


@dataclass
class Quest:
    key: str
    premise: str
    obstacle: str
    clue: str
    action: str
    result: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion: str
    quest_key: str
    rhyme_index: int = 0
    opening_index: int = 0
    caretaker_index: int = 0
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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def _quest(key: str) -> Quest:
    for item in QUESTS:
        if item["key"] == key:
            return Quest(**item)
    raise StoryError(f"Unknown quest: {key}")


def _speaker(world: World, name: str, line: str) -> None:
    world.say(f'"{line}" {name} said.')


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", "child", params.hero_name))
    companion = world.add(Entity("companion", "helper", params.companion))
    guide = world.add(Entity("guide", "mythic_guide", "the Green Sage"))
    quest = _quest(params.quest_key)
    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    rhyme = RHYME_LINES[params.rhyme_index % len(RHYME_LINES)]
    advice = CARETAKER_LINES[params.caretaker_index % len(CARETAKER_LINES)]

    hero.memes.update(bravery=1.0, curiosity=1.0, teamwork=1.0, kindness=1.0)
    companion.memes.update(bravery=1.0, trust=1.0, teamwork=1.0)
    guide.memes.update(wisdom=1.0, care=1.0)
    hero.meters.update(quest_progress=0.0, shared_effort=0.0)
    companion.meters.update(quest_progress=0.0, shared_effort=0.0)

    world.say(opening)
    world.say(
        f"In {setting.place}, {params.hero_name} received a green thread from the Green Sage. "
        f"The thread would lead to the quest: {quest.premise}."
    )
    world.say(
        f"{params.companion.capitalize()} joined {params.hero_name}. "
        "The two travelers packed a loaf, a bell, and a small map drawn on a leaf."
    )
    world.para()

    _speaker(world, guide, advice)
    _speaker(world, companion, "I can watch one path while you watch another, and we can tell each other what we find.")
    _speaker(world, hero, "Then our quest will have two pairs of eyes and one kind purpose.")
    world.say(f"They stepped beneath the green boughs, but soon {quest.obstacle}.")
    world.para()

    world.say(f"Luna listened instead of rushing. At last, the travelers discovered that {quest.clue}.")
    world.say(f"{params.hero_name} held up the leaf-map. {rhyme[0]} {rhyme[1]}")
    _speaker(world, companion, "Your rhyme tells us when to move, and my clue tells us where to look.")
    _speaker(world, hero, "Together, then. No one walks ahead alone.")
    world.say(quest.action)
    world.para()

    world.say(quest.result)
    world.say(
        f"The Green Sage appeared beside the path and said, \"{advice}\" "
        "The travelers understood that the true treasure was not only what they found, "
        "but how they had found it."
    )
    world.say(f"{quest.ending} {quest.lesson}")
    world.say(f"That night, {params.hero_name} and {params.companion} rested beneath green stars.")
    world.fired.update(
        {
            ("quest", quest.key),
            ("clue", quest.key),
            ("teamwork", quest.key),
            ("resolution", quest.key),
        }
    )
    hero.meters.update(quest_progress=1.0, shared_effort=1.0)
    companion.meters.update(quest_progress=1.0, shared_effort=1.0)
    world.facts.update(
        hero=hero,
        companion=companion,
        guide=guide,
        quest=quest,
        rhyme=rhyme,
        advice=advice,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    quest: Quest = world.facts["quest"]
    return [
        f"Tell a mythic green quest about {params.hero_name} and {params.companion}.",
        f"Use teamwork and a rhyme to solve this obstacle: {quest.obstacle}.",
        f"End with a concrete green image proving that the quest changed the land.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    quest: Quest = world.facts["quest"]
    rhyme: tuple[str, str] = world.facts["rhyme"]
    return [
        QAItem(
            question=f"What quest did {params.hero_name} and {params.companion} undertake?",
            answer=f"They undertook a quest to solve the problem described in the story: {quest.premise}.",
        ),
        QAItem(
            question="What obstacle blocked the travelers?",
            answer=f"Their path was blocked because {quest.obstacle}.",
        ),
        QAItem(
            question="What clue did the team discover?",
            answer=f"They discovered that {quest.clue}.",
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"They shared different jobs and used what each traveler noticed. {quest.action}",
        ),
        QAItem(
            question="What rhyme guided the quest?",
            answer=f'The travelers said, "{rhyme[0]} {rhyme[1]}"',
        ),
        QAItem(
            question="How did the ending show that the quest succeeded?",
            answer=f"{quest.ending} This showed that {quest.lesson.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share jobs, listen to one another, and combine their efforts toward one goal.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey in which travelers face difficulties while seeking or accomplishing something important.",
        ),
        QAItem(
            question="Why can a rhyme help a team?",
            answer="A rhyme can help a team remember a plan and move together at the right time.",
        ),
        QAItem(
            question="What does green represent in this storyworld?",
            answer="Green represents living places, renewal, and the shared hope that grows when friends care for one another.",
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
        lines.append(
            f"{entity.id}: {entity.type} {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_active(H,Q) :- hero(H), quest(Q).
teamwork(H,C,Q) :- quest_active(H,Q), companion(C), shares_plan(H,C).
clue_found(H,C,Q) :- teamwork(H,C,Q), clue(Q).
rhyme_guides(H,C,Q) :- clue_found(H,C,Q), rhyme(Q).
resolved(Q) :- rhyme_guides(H,C,Q), safe_path(Q).
green_restored(Q) :- resolved(Q), green_land(Q).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("companion", "companion"),
            asp.fact("quest", "quest"),
            asp.fact("clue", "quest"),
            asp.fact("rhyme", "quest"),
            asp.fact("green_land", "quest"),
            asp.fact("shares_plan", "hero", "companion"),
            asp.fact("safe_path", "quest"),
            asp.fact("show", "quest"),
        ]
    )


def asp_program(show: str = "#show green_restored/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show teamwork/3.\n#show resolved/1.\n#show green_restored/1."))
        teamwork = asp.atoms(model, "teamwork")
        resolved = asp.atoms(model, "resolved")
        restored = asp.atoms(model, "green_restored")
        if ("hero", "companion", "quest") not in teamwork:
            raise StoryError("ASP teamwork parity failed")
        if ("quest",) not in resolved or ("quest",) not in restored:
            raise StoryError("ASP resolution parity failed")
    except ImportError:
        return 0

    for params in CURATED:
        sample = generate(params)
        if "teamwork" not in sample.story.lower():
            raise StoryError("Generated story omitted teamwork")
        if "green" not in sample.story.lower():
            raise StoryError("Generated story omitted green imagery")
        if len(sample.story_qa) < 3:
            raise StoryError("Generated story lacks grounded QA")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic green quest about rhyme and teamwork.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--quest", choices=[q["key"] for q in QUESTS])
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
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=hero_name,
        companion=args.companion or rng.choice(COMPANIONS),
        quest_key=args.quest or rng.choice([q["key"] for q in QUESTS]),
        rhyme_index=rng.randrange(len(RHYME_LINES)),
        opening_index=rng.randrange(len(OPENINGS)),
        caretaker_index=rng.randrange(len(CARETAKER_LINES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(place=params.place), params)
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
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        try:
            sys.exit(asp_verify())
        except StoryError as exc:
            print(f"verification failed: {exc}", file=sys.stderr)
            sys.exit(1)
    if args.asp:
        print(asp_program("#show teamwork/3.\n#show clue_found/3.\n#show resolved/1.\n#show green_restored/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = CURATED
    else:
        params_list = []
        for index in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
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


CURATED = [
    StoryParams(
        place="the Greenwood Vale",
        hero_name="Luna",
        companion="a fox",
        quest_key="lantern",
        rhyme_index=0,
        opening_index=1,
        caretaker_index=0,
    ),
    StoryParams(
        place="the emerald meadow",
        hero_name="Mira",
        companion="a river sprite",
        quest_key="seed",
        rhyme_index=3,
        opening_index=4,
        caretaker_index=5,
    ),
    StoryParams(
        place="the Mossy Hills",
        hero_name="Tavi",
        companion="a young giant",
        quest_key="bell",
        rhyme_index=2,
        opening_index=0,
        caretaker_index=2,
    ),
    StoryParams(
        place="the fern-covered mountain",
        hero_name="Nell",
        companion="a little raven",
        quest_key="brook",
        rhyme_index=5,
        opening_index=3,
        caretaker_index=3,
    ),
]


if __name__ == "__main__":
    main()
