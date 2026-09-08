#!/usr/bin/env python3
"""
A small animal storyworld about a petite mouse, a magic plate, and reconciliation.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    animal: str
    friend: str
    plate: str
    magic: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


PLACES = {
    "mossy_kitchen": Place("mossy_kitchen", "the mossy kitchen", {"plate"}),
    "moonlit_garden": Place("moonlit_garden", "the moonlit garden", {"plate"}),
    "acorn_hall": Place("acorn_hall", "the acorn hall", {"plate"}),
}

ANIMALS = {
    "Luna": ("mouse", "she"),
    "Pip": ("rabbit", "he"),
    "Tilly": ("squirrel", "she"),
    "Bramble": ("hedgehog", "he"),
    "Nora": ("field mouse", "she"),
    "Otis": ("otter", "he"),
}

FRIENDS = list(ANIMALS)
PLATES = {
    "moon_plate": {
        "label": "a little moon-white plate",
        "gift": "a warm silver glow",
        "clue": "a crescent mark around its rim",
    },
    "berry_plate": {
        "label": "a petite berry-red plate",
        "gift": "a sweet berry scent",
        "clue": "three berry dots beneath its edge",
    },
    "star_plate": {
        "label": "a tiny star-speckled plate",
        "gift": "a bright golden sparkle",
        "clue": "a star pressed into its center",
    },
}

MAGIC = {
    "glow": {
        "label": "the magic of gentle light",
        "power": "glow softly when honest words are spoken",
        "ending": "Its light turned the dark table silver.",
    },
    "song": {
        "label": "the magic of a listening song",
        "power": "hum a small tune when two friends truly listen",
        "ending": "Its tune curled through the room like a friendly breeze.",
    },
    "kindness": {
        "label": "the magic of shared kindness",
        "power": "fill an empty cup whenever someone makes amends",
        "ending": "A bright cup of tea appeared for everyone to share.",
    },
}

ARCS = {
    "crumb": {
        "opening": "Luna was the petite keeper of a shining plate.",
        "problem": "One morning, Pip bumped the table, and the plate slid into a bowl of crumbs.",
        "hurt": "Luna thought Pip had been careless on purpose, while Pip felt too ashamed to explain.",
        "turn": "The plate's crescent mark glimmered and showed the path of the crumb that had made Pip sneeze.",
        "repair": "Pip swept the crumbs away, and Luna helped mend the plate's little rim with honey-colored clay.",
    },
    "rain": {
        "opening": "Luna carried the petite plate beneath a leaf umbrella.",
        "problem": "A sudden rain shower washed the plate from her paws and carried it toward the brook.",
        "hurt": "Tilly had grabbed the wrong end of the umbrella, and both friends blamed each other.",
        "turn": "The plate's magic made a silver trail on the water, revealing that the umbrella cord had tangled them together.",
        "repair": "Tilly pulled the cord free, and Luna thanked her for holding on when the current grew strong.",
    },
    "feast": {
        "opening": "Luna polished the petite plate for the woodland supper.",
        "problem": "Bramble tasted the berry tart before supper, leaving one neat bite missing.",
        "hurt": "Luna believed Bramble had spoiled her special dish, so she turned her back on him.",
        "turn": "The plate's berry dots shimmered and revealed that Bramble had taken the bite to share with a shivering field mouse.",
        "repair": "Bramble admitted he should have asked first, and Luna invited the field mouse to the table.",
    },
    "shadow": {
        "opening": "Luna found the petite plate beside the old oak at twilight.",
        "problem": "A long shadow made it seem that Pip had hidden the plate behind a root.",
        "hurt": "Luna accused Pip, and Pip hurried away with his ears drooping.",
        "turn": "The magic plate cast a small beam that showed the shadow belonged to a branch, not Pip.",
        "repair": "Luna found Pip, apologized clearly, and listened while he explained where he had really been.",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="An animal story about a petite plate and reconciliation magic.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--animal", choices=sorted(ANIMALS))
    parser.add_argument("--friend", choices=sorted(FRIENDS))
    parser.add_argument("--plate", choices=sorted(PLATES))
    parser.add_argument("--magic", choices=sorted(MAGIC))
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [
        (place, animal, friend, plate, magic)
        for place in PLACES
        for animal in ANIMALS
        for friend in FRIENDS
        for plate in PLATES
        for magic in MAGIC
        if animal != friend and "plate" in PLACES[place].affords
    ]


ASP_RULES = r"""
place(P) :- place_name(P).
animal(A) :- animal_name(A).
friend(F) :- animal_name(F).
plate(K) :- plate_name(K).
magic(M) :- magic_name(M).
valid_story(P,A,F,K,M) :-
    place(P), animal(A), friend(F), plate(K), magic(M), A != F.
#show valid_story/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place_name", place))
    for animal in ANIMALS:
        lines.append(asp.fact("animal_name", animal))
    for plate in PLATES:
        lines.append(asp.fact("plate_name", plate))
    for magic in MAGIC:
        lines.append(asp.fact("magic_name", magic))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        clingo_values = set(asp_valid_stories())
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    if py == clingo_values:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("ASP/Python mismatch.")
    print("Only in Python:", sorted(py - clingo_values))
    print("Only in ASP:", sorted(clingo_values - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        item for item in valid_combos()
        if args.place is None or item[0] == args.place
        if args.animal is None or item[1] == args.animal
        if args.friend is None or item[2] == args.friend
        if args.plate is None or item[3] == args.plate
        if args.magic is None or item[4] == args.magic
    ]
    if not choices:
        raise StoryError("No valid story matches the requested choices.")
    place, animal, friend, plate, magic = rng.choice(choices)
    return StoryParams(place, animal, friend, plate, magic)


def generate(params: StoryParams) -> StorySample:
    if params.animal == params.friend:
        raise StoryError("The two animals must be different so reconciliation can occur.")

    place = PLACES[params.place]
    plate_info = PLATES[params.plate]
    magic_info = MAGIC[params.magic]
    arc = ARCS[params.magic if params.magic in ARCS else "crumb"]
    animal_kind, animal_pronoun = ANIMALS[params.animal]
    friend_kind, friend_pronoun = ANIMALS[params.friend]

    world = World(place)
    animal = world.add(Entity(params.animal, "animal", params.animal))
    friend = world.add(Entity(params.friend, "animal", params.friend))
    plate = world.add(Entity("plate", "object", plate_info["label"]))
    animal.memes["trust"] = 0.2
    friend.memes["trust"] = 0.2
    plate.meters["magic"] = 1.0
    world.facts.update(
        animal=animal,
        friend=friend,
        plate=plate,
        animal_kind=animal_kind,
        friend_kind=friend_kind,
        pronoun=animal_pronoun,
        friend_pronoun=friend_pronoun,
        plate_info=plate_info,
        magic_info=magic_info,
        arc=arc,
        reconciled=False,
    )

    story = [
        f"{arc['opening']} {params.animal} was a {animal_kind}, and {params.friend} was a {friend_kind} who lived nearby.",
        f"They were preparing a small meal in {place.label}, where {plate_info['label']} was meant to hold the first helping.",
        f"The plate carried {plate_info['clue']}, and it had {magic_info['label']}: it could {magic_info['power']}.",
        arc["problem"],
        arc["hurt"],
        f'"I wish you would tell me what happened," said {params.animal}.',
        f'"I was afraid you would be angry," said {params.friend}. "But I want to make things right."',
        f"{arc['turn']} The magic did not choose a side; it helped both friends see the truth.",
        f'"I am sorry I blamed you before listening," said {params.animal}.',
        f'"I am sorry I did not speak up," said {params.friend}.',
        arc["repair"],
        f"They worked together until the plate was safe again. {params.animal} and {params.friend} touched paws, and their trust grew from {0.2:.1f} to {1.0:.1f}.",
        f"They shared the meal from the plate. {magic_info['ending']}",
        "From then on, when a small trouble appeared, they asked questions before making accusations.",
    ]

    animal.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    plate.meters["repaired"] = 1.0
    world.facts["reconciled"] = True
    world.facts["story"] = " ".join(story)

    prompts = [
        "Write a gentle animal story about a petite friend, a plate, and reconciliation.",
        f"Show how {params.animal} and {params.friend} repair their friendship after a misunderstanding.",
        f"Use {plate_info['label']} and {magic_info['label']} as magical story instruments.",
    ]

    story_qa = [
        QAItem(
            f"What was special about the plate?",
            f"The plate was {plate_info['label']}, and it had {magic_info['label']}: it could {magic_info['power']}.",
        ),
        QAItem(
            f"What caused the trouble between {params.animal} and {params.friend}?",
            f"{arc['problem']} {params.animal} misunderstood what had happened and felt hurt.",
        ),
        QAItem(
            "How did the magic help?",
            f"{arc['turn']} It helped the friends discover the truth instead of staying angry.",
        ),
        QAItem(
            f"How did {params.animal} and {params.friend} reconcile?",
            f"They spoke honestly, apologized for their parts, and worked together. {arc['repair']}",
        ),
        QAItem(
            "What changed at the end?",
            f"The plate was safe, the meal was shared, and both animals' trust grew because they listened before blaming.",
        ),
    ]

    world_qa = [
        QAItem("What is reconciliation?", "Reconciliation is making peace after a disagreement by telling the truth, listening, and repairing the harm."),
        QAItem("What does petite mean?", "Petite means small and delicately sized."),
        QAItem("What is magic in a story?", "Magic is a wondrous power that makes unusual events possible and helps reveal the story's meaning."),
        QAItem("Why is listening useful during an argument?", "Listening helps people learn what really happened and choose a fair, kind response."),
    ]

    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place: {world.place.label}")
    for entity in world.entities.values():
        lines.append(f"{entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}")
    lines.append(f"reconciled: {world.facts.get('reconciled')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("mossy_kitchen", "Luna", "Pip", "moon_plate", "glow"),
    StoryParams("moonlit_garden", "Luna", "Tilly", "berry_plate", "rain"),
    StoryParams("acorn_hall", "Luna", "Bramble", "star_plate", "feast"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("Generated-story verification failed.")
                sys.exit(1)
        print("OK: generated stories are complete.")
        return

    if args.asp:
        try:
            values = asp_valid_stories()
        except ImportError:
            print("ASP mode requires clingo.")
            sys.exit(1)
        print(f"{len(values)} valid story combinations:")
        for value in values[:20]:
            print(" ", value)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(seed + index)
            params = resolve_params(args, rng)
            params.seed = seed + index
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
