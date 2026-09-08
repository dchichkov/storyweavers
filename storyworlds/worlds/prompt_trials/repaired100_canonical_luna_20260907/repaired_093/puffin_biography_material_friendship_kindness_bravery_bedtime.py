#!/usr/bin/env python3
"""
A bedtime storyworld about a puffin who learns that a biography is made from
kind choices, brave moments, and the friendship that remembers them.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    material: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Luna", "Pip", "Milo", "Nell", "Tavi", "Rumi", "Cora", "Finn"]
FRIEND_NAMES = ["Bram", "Nori", "Mara", "Ollie", "Suki", "Tess", "Pia", "Juno"]
MATERIALS = ["blue wool", "soft linen", "silver thread", "red felt", "green sea-cloth"]

EPISODES = [
    {
        "id": "lantern",
        "place": "a moonlit island library",
        "material_use": "a small blue wool bookmark",
        "need": "the oldest lantern had gone dark",
        "kindness": "Luna shared her warm nest lining with a shivering young gull",
        "bravery": "she crossed the quiet library floor during a thunderstorm to fetch the spare wick",
        "truth": "the dark lantern needed a new wick, not a new flame",
        "ending": "the lantern glowed beside the open biography while waves whispered below",
        "lesson": "A brave heart can carry kindness through the dark.",
    },
    {
        "id": "map",
        "place": "a snug cliffside reading room",
        "material_use": "a red felt map case",
        "need": "the bedtime map had torn along its brightest path",
        "kindness": "Luna invited a lonely seal pup to sit beside her",
        "bravery": "she climbed to the high craft shelf while the wind rattled the windows",
        "truth": "the map could be mended with a careful strip of sea-cloth",
        "ending": "the repaired map rested under the stars, showing every safe way home",
        "lesson": "Kindness helps us notice who needs a place, and bravery helps us mend what matters.",
    },
    {
        "id": "blanket",
        "place": "a warm burrow beneath the lighthouse",
        "material_use": "a silver-thread blanket",
        "need": "the youngest puffin could not settle for sleep",
        "kindness": "Luna listened while the little puffin described a frightening dream",
        "bravery": "she stepped outside to face the lonely foghorn and learn its sound",
        "truth": "the foghorn was a warning for boats, not a monster near the burrow",
        "ending": "the silver-thread blanket shimmered while every puffin slept safely",
        "lesson": "Understanding a fear can make room for calm.",
    },
    {
        "id": "journal",
        "place": "a candlelit room above the harbor",
        "material_use": "green sea-cloth covers for a journal",
        "need": "the family biography had loose pages",
        "kindness": "Luna thanked the old keeper for every story he remembered",
        "bravery": "she asked aloud about a mistake that everyone else had been avoiding",
        "truth": "the missing page told how an earlier puffin had repaired the harbor bell",
        "ending": "the biography closed gently, holding both the mistake and the courage that followed",
        "lesson": "A true biography makes room for difficult moments and the kindness that changes them.",
    },
]

OPENINGS = [
    "When the moon climbed above the island, {hero} tucked a tiny notebook beneath her wing.",
    "At bedtime, {hero} found an old book beside the window and carried it to the softest nest.",
    "The lighthouse keeper had just lowered the evening lamp when {hero} began a quiet reading adventure.",
    "Before sleep, {hero} promised {friend} that they would discover whose life the old book remembered.",
]

REFLECTIONS = [
    '"A biography is more than a list of days," said {friend}. "It shows the choices inside them."',
    '"Then tonight can become part of my story," {hero} whispered. "I can choose kindness again."',
    '"You were frightened and still helped," {friend} said. "That is what bravery looked like."',
    '{hero} touched the material gently. "Small things can hold big memories when friends care for them."',
]


ASP_RULES = r"""
has_friendship :- friend_support.
has_kindness :- kind_choice.
has_bravery :- brave_choice.
biography_complete :- has_friendship, has_kindness, has_bravery, material_present.
valid_story :- biography_complete.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("character", "puffin"),
        asp.fact("genre", "biography"),
        asp.fact("material", "story_material"),
        asp.fact("friend_support"),
        asp.fact("kind_choice"),
        asp.fact("brave_choice"),
        asp.fact("material_present"),
    ])


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    episode = rng.choice(EPISODES)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)

    world = World()
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="puffin",
        label="puffin",
        meters={"steps": 0.0, "distance": 0.0},
        memes={"friendship": 1.0, "kindness": 0.0, "bravery": 0.0, "worry": 0.0, "peace": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="puffin",
        label="friend puffin",
        meters={"steps": 0.0},
        memes={"friendship": 1.0, "kindness": 1.0, "bravery": 0.0},
    ))
    material = world.add(Entity(
        id="material",
        kind="thing",
        type="material",
        label=params.material,
        meters={"softness": 1.0, "warmth": 1.0},
        memes={},
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        material=material,
        episode=episode,
        opening=opening,
        reflection=reflection,
    )
    return world


def tell_beginning(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    material = world.facts["material"]
    episode = world.facts["episode"]

    world.say(world.facts["opening"].format(hero=hero.id, friend=friend.id))
    world.say(
        f"The book was a biography about an old puffin who had once cared for {episode['place']}. "
        f"Its cover was wrapped in {material.label}, soft as a sleepy cloud."
    )
    world.say(
        f"{friend.id} settled close. \"A biography tells what someone did,\" {friend.id} said. "
        "\"Let us see which choices made this puffin's life worth remembering.\""
    )
    world.say(f"On the next page, they read that {episode['need']}.")
    hero.memes["worry"] += 1
    hero.meters["steps"] += 1
    world.facts["need"] = episode["need"]


def tell_middle(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    episode = world.facts["episode"]

    world.say(f"First, the biography described how {episode['kindness']}.")
    hero.memes["kindness"] += 1
    world.say(
        f"Then a sudden sound made the room tremble. {episode['bravery'].capitalize()}. "
        f"{hero.id}'s feathers quivered, but {friend.id} followed close behind."
    )
    hero.memes["bravery"] += 1
    hero.meters["distance"] += 3
    friend.memes["bravery"] += 0.5
    world.say(
        f'"Should we turn back?" asked {friend.id}. '
        f'"We can be careful and still continue," answered {hero.id}. '
        f'"We will help each other."'
    )
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(f"Together they discovered that {episode['truth']}.")
    hero.memes["worry"] = 0
    hero.memes["peace"] += 1
    world.facts["truth"] = episode["truth"]


def tell_resolution(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    material = world.facts["material"]
    episode = world.facts["episode"]

    world.say(world.facts["reflection"].format(hero=hero.id, friend=friend.id))
    world.say(
        f"{hero.id} used the {material.label} to mark the page, so no one would forget "
        f"how kindness, friendship, and bravery had shaped the old puffin's biography."
    )
    world.say(
        f"At last, {episode['ending']}. {friend.id} tucked one wing around {hero.id}, "
        "and the two friends drifted into a peaceful sleep."
    )
    hero.memes["peace"] += 1
    world.facts["resolved"] = True
    world.facts["lesson"] = episode["lesson"]
    world.facts["ending"] = episode["ending"]


def generate_world(params: StoryParams) -> World:
    world = build_world(params)
    tell_beginning(world)
    tell_middle(world)
    tell_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    material = world.facts["material"]
    episode = world.facts["episode"]
    return [
        "Write a gentle Bedtime Story about a puffin discovering that a biography is made from meaningful choices.",
        f"Show how {hero.id} and {friend.id} use Friendship, Kindness, and Bravery while caring for {episode['place']}.",
        f"Include {material.label} as a material object that helps preserve the memory, and end with {episode['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    material = world.facts["material"]
    episode = world.facts["episode"]
    return [
        QAItem(
            question=f"What was {hero.id} reading before bedtime?",
            answer=f"{hero.id} was reading a biography about an old puffin whose choices had cared for {episode['place']}."
        ),
        QAItem(
            question=f"What material helped mark or protect the biography?",
            answer=f"The biography was connected with {material.label}, a soft material that helped preserve the important page."
        ),
        QAItem(
            question=f"How did {hero.id} show kindness?",
            answer=f"{hero.id} showed kindness when {episode['kindness']}."
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery when {episode['bravery']}."
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id}?",
            answer=f"{friend.id} stayed close, asked a careful question, and helped {hero.id} continue safely. Their Friendship made the difficult moment less frightening."
        ),
        QAItem(
            question="What did the puffins discover?",
            answer=f"They discovered that {episode['truth']}. This changed worry into understanding."
        ),
        QAItem(
            question="What lesson did the biography teach?",
            answer=episode["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puffin?",
            answer="A puffin is a small seabird with a colorful bill that lives near cold northern seas."
        ),
        QAItem(
            question="What is a biography?",
            answer="A biography is a true account of another person's life, including important events and choices."
        ),
        QAItem(
            question="What is material?",
            answer="Material is the substance from which something is made, such as wool, cloth, wood, or metal."
        ),
        QAItem(
            question="How can Friendship, Kindness, and Bravery work together?",
            answer="Friendship gives someone support, Kindness notices and helps with another person's needs, and Bravery makes it possible to act carefully even when something feels frightening."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp
        model = asp.one_model(asp_program())
        valid = asp.atoms(model, "valid_story")
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    if not valid:
        print("MISMATCH: ASP produced no valid story.")
        return 1
    for seed in range(5):
        sample = generate(StoryParams("Luna", "Bram", "blue wool", seed))
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story exercise failed.")
            return 1
    print("OK: Python and ASP reasonableness gates pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Bedtime Story world about a puffin, a biography, and friendship."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--material", choices=MATERIALS)
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
    name = args.name or rng.choice(NAMES)
    friends = [n for n in FRIEND_NAMES if n != name]
    friend_name = args.friend_name or rng.choice(friends)
    material = args.material or rng.choice(MATERIALS)
    return StoryParams(name=name, friend_name=friend_name, material=material)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:8}) meters={meters} memes={memes}"
        )
    return "\n".join(lines)


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
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        values = asp.atoms(model, "valid_story")
        print(f"{len(values)} compatible stories:")
        for value in values:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Bram", "blue wool", base_seed),
            StoryParams("Milo", "Nori", "red felt", base_seed + 1),
            StoryParams("Cora", "Juno", "silver thread", base_seed + 2),
            StoryParams("Finn", "Mara", "green sea-cloth", base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

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
