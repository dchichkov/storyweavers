#!/usr/bin/env python3
"""
A small adventure world about a bright vest, a talking lantern, and a magical
bridge that appears only when friends share what they know.
"""

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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    terrain: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None
    quest: int = 0
    opening: int = 0
    warning: int = 0
    twist: int = 0
    ending: int = 0


SETTINGS = {
    "moonlit_valley": Setting(
        "the moonlit valley", "a narrow ravine", {"vest", "lantern", "bridge"}
    ),
    "whispering_forest": Setting(
        "the whispering forest", "a mossy trail", {"vest", "lantern", "bridge"}
    ),
    "cloud_mountain": Setting(
        "Cloud Mountain", "a windy cliff path", {"vest", "lantern", "bridge"}
    ),
}

HERO_NAMES = ["Luna", "Mara", "Tavi", "Nell", "Orin", "Sela"]
FRIEND_NAMES = ["Pip", "Rowan", "Milo", "Aya", "Juno", "Beck"]

QUESTS = [
    {
        "signal": "a blue star flickering beyond the trail",
        "wish": "reach the old tower before the star went dark",
        "danger": "step onto a broken stone path above the ravine",
        "clue": "the safest stones glowed only when both travelers stood still",
        "magic": "the trail was waiting for two honest voices",
        "twist": "the star was not a distant warning at all; it was a tiny door-lamp on the hidden bridge",
        "repair": "They crossed together and placed the star-lamp beside the tower door.",
        "lesson": "bravery grows stronger when friends share what they notice",
        "ending": "The bright vest shone beside the little star-lamp as the tower opened.",
    },
    {
        "signal": "a golden feather circling above the trees",
        "wish": "find the sky bird that had dropped it",
        "danger": "chase the feather onto a slippery ledge",
        "clue": "the feather floated toward the trail whenever they spoke calmly",
        "magic": "the mountain wind understood gentle words",
        "twist": "the feather belonged to a magical map folded inside the vest's pocket",
        "repair": "They unfolded the map and used it to guide a lost cloud-sprite home.",
        "lesson": "a mystery can become a kindness when we stop chasing and start listening",
        "ending": "The cloud-sprite waved from above while the feather rested safely in the vest pocket.",
    },
    {
        "signal": "green lights blinking under a fallen arch",
        "wish": "discover who had hung lanterns in the dark",
        "danger": "crawl beneath the unstable stones",
        "clue": "the lights blinked in the same rhythm as the lantern they carried",
        "magic": "their lantern could wake sleeping paths",
        "twist": "the arch was a sleeping dragon's curled tail, not a ruined gate",
        "repair": "They whispered an apology, walked around the dragon, and followed the newly lit path.",
        "lesson": "careful questions can keep an adventure safe for everyone",
        "ending": "The dragon snored softly while the vest and lantern led them home.",
    },
    {
        "signal": "a silver ribbon dancing between the pines",
        "wish": "follow it to a hidden treasure",
        "danger": "leave the marked trail without telling anyone",
        "clue": "the ribbon returned whenever they named the people waiting for them",
        "magic": "the forest tied safe travelers to the path with moonlight",
        "twist": "the treasure was a box of letters from children who had once walked there",
        "repair": "They carried the letters to the village keeper, who promised to deliver them.",
        "lesson": "the best treasure may be a message that helps someone feel remembered",
        "ending": "The silver ribbon curled around the vest as the friends carried the letters home.",
    },
]

OPENINGS = [
    "At first light, {hero} pulled on a red vest and set out with {friend} across {place}.",
    "The adventure began when {hero} fastened a sturdy vest and met {friend} at the edge of {place}.",
    "A cool wind swept through {place} as {hero} and {friend} prepared for one careful journey.",
    "With a lantern swinging between them, {hero} and {friend} entered {place} in search of a true adventure.",
]

WARNINGS = [
    '"We can be brave without being hasty," {hero} said. "Tell me what you see before we move."',
    '"Stay beside me," {friend} urged. "A magical clue is still a clue we must check."',
    '"Our feet wait while our eyes investigate," {hero} said, touching the bright vest.',
    '"No treasure is worth a foolish step," {friend} replied. "Let us find a safer way."',
]

TWISTS = [
    '"That was the twist!" {friend} cried. "The magic was helping us listen, not pulling us forward."',
    '"We thought we were following a signal," {hero} said, "but the signal was following our careful choices."',
    '"The secret was close all along," {friend} whispered. "It needed both of us to understand it."',
    '"A real adventure changes when the truth appears," {hero} said. "Now we know what to protect."',
]

ENDINGS = [
    '"Next time, we will bring the same courage and better questions," {friend} promised.',
    '"I will remember to share every clue," {hero} said, smoothing the vest.',
    '"The magic trusted us because we trusted one another," {friend} said.',
    '"We found our way by working together," {hero} replied.',
]


ASP_RULES = r"""
#show valid/2.
setting(moonlit_valley). setting(whispering_forest). setting(cloud_mountain).
affords(moonlit_valley,vest). affords(moonlit_valley,lantern). affords(moonlit_valley,bridge).
affords(whispering_forest,vest). affords(whispering_forest,lantern). affords(whispering_forest,bridge).
affords(cloud_mountain,vest). affords(cloud_mountain,lantern). affords(cloud_mountain,bridge).
valid(P, F) :- setting(P), affords(P, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        for feature in sorted(setting.affords):
            lines.append(asp.fact("affords", name, feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple]:
    return sorted((place, feature) for place, setting in SETTINGS.items() for feature in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py != clingo:
        print("MISMATCH between Python and ASP.")
        print("Only Python:", sorted(py - clingo))
        print("Only ASP:", sorted(clingo - py))
        return 1
    print(f"OK: ASP matches Python ({len(py)} valid combinations).")
    for place in SETTINGS:
        sample = generate(
            StoryParams(place, "VerifyHero", "VerifyFriend", quest=0, opening=0, warning=0, twist=0, ending=0)
        )
        if not sample.story or "vest" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print("OK: generated stories passed.")
    return 0


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    setting = SETTINGS[params.place]
    quest = QUESTS[params.quest % len(QUESTS)]
    world = StoryState(setting)

    hero = world.add(Entity(
        params.hero_name, "character", "child", traits=["brave", "observant"],
        meters={"energy": 8, "distance": 0}, memes={"courage": 2, "curiosity": 3}
    ))
    friend = world.add(Entity(
        params.friend_name, "character", "child", traits=["careful", "kind"],
        meters={"energy": 8, "distance": 0}, memes={"trust": 3, "caution": 2}
    ))
    vest = world.add(Entity(
        "bright_vest", "thing", "vest", "a bright red vest",
        traits=["sturdy", "warm", "magical"], owner=hero.id, worn_by=hero.id,
        meters={"warmth": 5}, memes={"confidence": 3}
    ))
    lantern = world.add(Entity(
        "lantern", "thing", "lantern", "a small lantern",
        traits=["glowing", "enchanted"], owner=friend.id, meters={"light": 4}, memes={"hope": 2}
    ))

    place = setting.place
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        hero=hero.id, friend=friend.id, place=place
    ))
    world.say(f"Beyond the first bend, they saw {quest['signal']}.")
    world.say(
        f'"{quest["wish"].capitalize()}," {hero.id} said. '
        f'"Then we will go carefully," {friend.id} answered.'
    )

    world.para()
    world.say(f"As they hurried, {quest['danger']} seemed to invite them.")
    world.say(WARNINGS[params.warning % len(WARNINGS)].format(
        hero=hero.id, friend=friend.id
    ))
    world.say(f"They stopped on the firm trail and noticed that {quest['clue']}.")
    world.say(
        f"The vest warmed against {hero.id}'s chest, and the lantern gave one clear golden blink."
    )
    world.say(
        f'"Maybe the magic is waiting for us to understand it," {hero.id} said. '
        f'"Then let us speak every clue aloud," {friend.id} replied.'
    )
    world.say(f"When they shared what they knew, {quest['magic']}.")
    world.facts["tension"] = quest["danger"]
    world.facts["method"] = "stopping, observing, and sharing clues"
    world.facts["magic_awakened"] = True

    world.para()
    world.say(quest["twist"].capitalize() + ".")
    world.say(TWISTS[params.twist % len(TWISTS)])
    world.say(quest["repair"])
    world.say(
        f'"{quest["lesson"].capitalize()}," {hero.id} said. '
        f'{ENDINGS[params.ending % len(ENDINGS)].format(hero=hero.id, friend=friend.id)}'
    )
    world.say(quest["ending"])

    world.facts.update(
        hero=hero,
        friend=friend,
        vest=vest,
        lantern=lantern,
        quest=quest,
        place=place,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    quest = world.facts["quest"]
    return [
        f"Write an adventure about {world.facts['hero'].id} wearing a magical vest in {world.facts['place']}.",
        f"Tell a child-friendly adventure where friends investigate {quest['signal']} through dialogue.",
        "Write a magical twist story in which careful teamwork changes the ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    hero = f["hero"].id
    friend = f["friend"].id
    return [
        QAItem(
            "Who wore the magical vest?",
            f"{hero} wore the bright vest. It gave {hero} confidence while the friends explored carefully.",
        ),
        QAItem(
            f"What did {hero} and {friend} notice?",
            f"They noticed {q['signal']}. They did not rush toward it; they stopped and shared their clues.",
        ),
        QAItem(
            "What was the magical twist?",
            f"{q['twist'].capitalize()}. The surprising truth changed their plan and helped them protect others.",
        ),
        QAItem(
            "How did dialogue help the adventure?",
            f"{hero} and {friend} spoke about what they saw, so they chose {f['method']} instead of taking the dangerous step.",
        ),
        QAItem(
            "How did the story end?",
            q["ending"],
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a vest?",
            "A vest is a piece of clothing worn over a shirt or other clothes. It can provide warmth, pockets, or protection.",
        ),
        QAItem(
            "What is magic in a story?",
            "Magic is an imaginary power that can make unusual things happen, such as waking a hidden bridge or making a lantern answer.",
        ),
        QAItem(
            "Why is dialogue useful during an adventure?",
            "Dialogue lets characters share clues, ask questions, and change one another's decisions.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.traits:
            details.append("traits=" + ",".join(entity.traits))
        if entity.owner:
            details.append(f"owner={entity.owner}")
        if entity.worn_by:
            details.append(f"worn_by={entity.worn_by}")
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id}: {entity.type} ({'; '.join(details)})")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if hero == friend:
        friend = rng.choice([name for name in FRIEND_NAMES if name != hero])
    return StoryParams(
        place=place,
        hero_name=hero,
        friend_name=friend,
        seed=args.seed,
        quest=rng.randrange(len(QUESTS)),
        opening=rng.randrange(len(OPENINGS)),
        warning=rng.randrange(len(WARNINGS)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld with a magical vest, dialogue, and a twist."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Valid combinations:")
        for place, feature in asp_valid():
            print(f"  {place:20} {feature}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                hero_name=f"{place.title()}Hero",
                friend_name=f"{place.title()}Friend",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n) and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
