#!/usr/bin/env python3
"""
A small bedtime storyworld about Luna, a least-loved palette, and a quiet quest
to solve a conflict with care.
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
ROOT = next((p for p in HERE.parents if (p / "results.py").is_file()), HERE)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Mira", "Tavi", "Nell", "Sami", "Pip"]
HELPER_POOL = ["Grandma", "Grandpa", "Aunt Rose", "Uncle Sol"]
ROOM_POOL = ["the little art room", "the moonlit attic", "the quiet kitchen"]
OBJECT_POOL = ["a moon", "a sleepy garden", "a blue boat", "a tiny dragon"]
PALETTES = ["least-loved pallette", "wooden pallette", "rainbow pallette"]


QUESTS = [
    {
        "goal": "paint a bedtime picture for the window",
        "conflict": "the least-loved pallette had been left dry and dusty beneath a chair",
        "clue": "a single silver-blue mark still shone in one corner",
        "failed": "grabbed the brightest paints from a fresh tray and began without asking",
        "turn": "Luna saw that the old pallette could still hold the colors needed for moonlight",
        "action": "cleaned the pallette, shared the fresh colors, and painted with everyone",
        "resolution": "The picture became a gentle moon above a house with every window glowing.",
        "ending": "By morning, the least-loved pallette rested on the sill, wearing a tiny stripe of moonlight.",
        "question": "What did Luna paint for the window?",
        "answer": "Luna painted a gentle moon above a house with every window glowing.",
    },
    {
        "goal": "make a star map for a stuffed bear's night voyage",
        "conflict": "Luna's least-loved pallette was claimed by two friends at the same time",
        "clue": "there was room for both hands if the colors were mixed in a careful circle",
        "failed": "pulled the pallette close and said it belonged only to her",
        "turn": "Luna realized the pallette was not a prize but a tool that could help the whole quest",
        "action": "made a sharing circle, mixed the colors, and invited each friend to add one star",
        "resolution": "The star map guided the stuffed bear safely across a painted midnight sky.",
        "ending": "The pallette slept beside the map, and its little wells looked like a row of quiet stars.",
        "question": "How did Luna solve the pallette conflict?",
        "answer": "Luna made a sharing circle, mixed the colors, and invited each friend to add one star.",
    },
    {
        "goal": "paint a tiny dragon who could guard bedtime dreams",
        "conflict": "the least-loved pallette had a cracked edge, and everyone blamed the last person who used it",
        "clue": "the crack was old, while the spilled green paint was still wet",
        "failed": "pointed at a friend before checking what had happened",
        "turn": "Luna understood that guessing could hurt someone, but careful looking could solve the problem",
        "action": "wiped the spill, examined the crack, and asked each friend what they had seen",
        "resolution": "The friends repaired the pallette with a soft ribbon and painted the dragon together.",
        "ending": "The ribboned pallette glimmered beside the sleeping dragon, ready for tomorrow's dreams.",
        "question": "What clue helped Luna understand the conflict?",
        "answer": "Luna noticed that the crack was old while the green paint was still wet.",
    },
]


THOUGHTS = [
    {
        "opening": "Tonight I will make something kind enough to help everyone sleep.",
        "worry": "If I hurry, the colors may become as tangled as my thoughts.",
        "turn": "A quiet look may show me what rushing hides.",
        "ending": "A gentle answer can be brighter than the brightest paint.",
    },
    {
        "opening": "Every quest begins with one small step and one careful breath.",
        "worry": "Perhaps I can win by holding everything tightly. Perhaps that is not a very good plan.",
        "turn": "The best clue is the one that lets everyone take part.",
        "ending": "The quest was finished because no one had to be left out.",
    },
    {
        "opening": "I will listen to the room before I ask the colors to speak.",
        "worry": "A quick guess feels easy, but easy is not always fair.",
        "turn": "The truth is waiting in a small detail.",
        "ending": "Kind questions mend more than paint pots.",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Grandma"
    room: str = "the little art room"
    pallette: str = "least-loved pallette"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("dust", "paint", "crack", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "frustration", "trust", "relief", "belonging"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(c) for c in "|".join(
        [params.name, params.helper, params.room, params.pallette]
    ))


def _capital(label: str) -> str:
    return label[:1].upper() + label[1:]


def tell_world(params: StoryParams) -> World:
    if params.pallette not in PALETTES:
        raise StoryError(f"Unknown pallette choice: {params.pallette}")
    rng = random.Random(_seed_number(params))
    quest = QUESTS[_seed_number(params) % len(QUESTS)]
    thought = THOUGHTS[(_seed_number(params) // len(QUESTS)) % len(THOUGHTS)]

    world = World(params.room)
    child = world.add(Entity(params.name, "character", params.name))
    helper = world.add(Entity("helper", "character", params.helper))
    pallette = world.add(Entity("pallette", "pallette", params.pallette))
    friend = world.add(Entity("friend", "character", "a friend"))
    world.facts.update(
        params=params,
        quest=quest,
        thought=thought,
        child=child,
        helper=helper,
        pallette=pallette,
        friend=friend,
        chosen_color=rng.choice(["blue", "silver", "violet", "green"]),
    )

    world.say(f"Near bedtime, {params.name} went to {params.room} to {quest['goal']}.")
    world.say(
        f"On the table waited a {params.pallette}, its little color wells quiet beneath a cloth."
    )
    world.say(f'{params.name} thought, "{thought["opening"]}"')
    world.para()

    child.memes["worry"] = 1
    child.memes["frustration"] = 1
    pallette.meters["dust"] = 1
    world.say(f"But {quest['conflict']}.")
    world.say(f"Trying to finish quickly, {params.name} {quest['failed']}.")
    world.say(f'{params.name} thought, "{thought["worry"]}"')
    world.say(
        f'{_capital(params.helper)} came close and said, "Before we choose a side, what do you notice?"'
    )
    world.say(f'{params.name} answered, "I notice {quest["clue"]}."')
    world.para()

    world.say(f'{_capital(params.helper)} smiled. "Then that clue can guide our next step."')
    world.say(f'{params.name} thought, "{thought["turn"]}"')
    world.say(f"Together, they {quest['action']}.")
    child.memes["worry"] = 0
    child.memes["frustration"] = 0
    child.memes["trust"] = 1
    child.memes["relief"] = 1
    child.memes["belonging"] = 1
    pallette.meters["dust"] = 0
    pallette.meters["paint"] = 1
    world.say(quest["resolution"])
    world.say(
        f'{params.name} said, "The pallette was not the least important thing after all."'
    )
    world.say(f'{_capital(params.helper)} replied, "Neither was anyone in this room."')
    world.say(f'{params.name} thought, "{thought["ending"]}"')
    world.para()
    world.say(quest["ending"])

    world.facts.update(
        resolved=True,
        clue=quest["clue"],
        solution=quest["action"],
        ending=quest["ending"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    quest = world.facts["quest"]
    return [
        f"Write a bedtime story about {params.name} on a quest to {quest['goal']}.",
        f"Tell a gentle Problem Solving story in which a conflict over a {params.pallette} is repaired.",
        f"Create a child-friendly bedtime Quest where careful listening changes what {params.name} does.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    quest = world.facts["quest"]
    return [
        QAItem(
            f"What was {params.name}'s bedtime quest?",
            f"{params.name}'s quest was to {quest['goal']}.",
        ),
        QAItem(
            "What conflict interrupted the quest?",
            f"The conflict was that {quest['conflict']}.",
        ),
        QAItem(
            "What clue helped solve the problem?",
            f"The helpful clue was that {quest['clue']}.",
        ),
        QAItem(
            "How did the friends repair the conflict?",
            f"They {quest['action']}.",
        ),
        QAItem(
            "What changed at the end?",
            quest["ending"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a pallette used for?",
            "A pallette is a surface where an artist places and mixes paints.",
        ),
        QAItem(
            "What is problem solving?",
            "Problem solving means noticing a difficulty, looking for useful clues, and choosing an action that can improve it.",
        ),
        QAItem(
            "Why is listening helpful during a conflict?",
            "Listening helps people learn what happened and find a fair answer instead of guessing or blaming.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
solved(Child) :- quest(Child), clue_used(Child), shared(Pallette).
peaceful(Child) :- solved(Child).
valid_pallette(least_loved_pallette).
valid_pallette(wooden_pallette).
valid_pallette(rainbow_pallette).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("quest", "luna"),
            asp.fact("clue_used", "luna"),
            asp.fact("shared", "least_pallette"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show peaceful/1."))
    found = set(asp.atoms(model, "peaceful"))
    expected = {("luna",)}
    if found != expected:
        print(f"MISMATCH between ASP and Python facts: ASP={found} PY={expected}")
        return 1
    for seed in range(5):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or "bedtime" not in " ".join(sample.prompts).lower():
            print("Generated story verification failed.")
            return 1
    print("OK: ASP parity and generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle bedtime problem-solving storyworld."
    )
    parser.add_argument("--name", choices=NAME_POOL)
    parser.add_argument("--helper", choices=HELPER_POOL)
    parser.add_argument("--room", choices=ROOM_POOL)
    parser.add_argument("--pallette", choices=PALETTES)
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
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        room=args.room or rng.choice(ROOM_POOL),
        pallette=args.pallette or rng.choice(PALETTES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program("#show peaceful/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show peaceful/1."))
        print(sorted(asp.atoms(model, "peaceful")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, pallette in enumerate(PALETTES):
            params = StoryParams(
                name=NAME_POOL[index % len(NAME_POOL)],
                helper=HELPER_POOL[index % len(HELPER_POOL)],
                room=ROOM_POOL[index % len(ROOM_POOL)],
                pallette=pallette,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 50):
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
