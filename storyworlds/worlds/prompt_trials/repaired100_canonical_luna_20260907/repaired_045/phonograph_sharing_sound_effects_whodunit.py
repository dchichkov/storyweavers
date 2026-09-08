#!/usr/bin/env python3
"""
A child-friendly whodunit about a phonograph, shared sounds, and a missing bell.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective: str
    helper: str
    suspects: tuple[str, str, str]
    place: str
    sound: str
    object: str
    seed: Optional[int] = None
    variant: int = 0


DETECTIVES = ["Luna", "Milo", "Ivy", "Nora", "Theo", "Zara"]
HELPERS = ["Pip", "Bea", "Ollie", "June", "Sam", "Tess"]
SUSPECT_GROUPS = [
    ("Mr. Finch", "Mara Mouse", "Grandpa Fox"),
    ("Basil Badger", "Cora Crow", "Nell Newt"),
    ("Aunt Dot", "Penny Hare", "Rufus Raccoon"),
]
PLACES = ["the Moonlit Clubhouse", "the Lantern Library", "the Rainy-Day Hall"]
SOUNDS = ["a creaky door", "three tapping spoons", "a train whistle", "a sleepy snore"]
OBJECTS = ["the brass bell", "the silver music box", "the red ribbon"]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a sharing-and-sound-effects phonograph whodunit."
    )
    parser.add_argument("--detective")
    parser.add_argument("--helper")
    parser.add_argument("--place")
    parser.add_argument("--sound")
    parser.add_argument("--object")
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
    detective = args.detective or rng.choice(DETECTIVES)
    helper_choices = [name for name in HELPERS if name != detective]
    suspects = rng.choice(SUSPECT_GROUPS)
    return StoryParams(
        detective=detective,
        helper=args.helper or rng.choice(helper_choices),
        suspects=suspects,
        place=args.place or rng.choice(PLACES),
        sound=args.sound or rng.choice(SOUNDS),
        object=args.object or rng.choice(OBJECTS),
        seed=args.seed,
        variant=rng.randrange(1_000_000_000),
    )


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(
        Entity(
            "detective",
            "character",
            params.detective,
            memes={"curiosity": 0.8, "fairness": 0.7},
        )
    )
    world.add(
        Entity(
            "helper",
            "character",
            params.helper,
            memes={"listening": 0.8, "sharing": 0.7},
        )
    )
    for index, name in enumerate(params.suspects, start=1):
        world.add(Entity(f"suspect_{index}", "character", name))
    world.add(
        Entity(
            "phonograph",
            "instrument",
            "the phonograph",
            owner="club",
            meters={"volume": 0.7, "needle_ready": 1.0},
            memes={"shared_music": 1.0},
        )
    )
    world.add(
        Entity(
            "missing_object",
            "object",
            params.object,
            owner="club",
            meters={"present": 0.0},
        )
    )
    return world


def tell(world: World) -> World:
    p = world.params
    detective, helper = p.detective, p.helper
    first, second, third = p.suspects
    rng = random.Random((p.seed or 0) ^ p.variant ^ 0x45A17)

    sound_effects = [
        f"The phonograph played a soft {p.sound}.",
        f"From the phonograph came a tiny sound effect: {p.sound}.",
        f"The needle crackled, and the phonograph answered with {p.sound}.",
    ]
    opening = rng.choice(
        [
            f"At {p.place}, {detective} and {helper} shared a table beside an old phonograph.",
            f"{detective} was showing {helper} how to share the phonograph fairly at {p.place}.",
            f"The friends had gathered at {p.place} for a listening party with one treasured phonograph.",
        ]
    )
    world.events.append(opening)
    world.events.append(
        f"They took turns choosing records, so everyone could enjoy the music."
    )
    world.events.append(rng.choice(sound_effects))
    world.events.append(
        f"Then the club keeper gasped: {p.object} had vanished from the shelf."
    )

    world.events.append(
        f"Three guests stood nearby: {first}, {second}, and {third}."
    )
    world.events.append(
        f'"I heard the phonograph make {p.sound}," said {first}.'
    )
    world.events.append(
        f'"I was sharing a record with {helper}," said {second}.'
    )
    world.events.append(
        f'"And I heard a click after the music stopped," said {third}.'
    )
    world.events.append(
        f'"We should listen carefully instead of blaming anyone," {detective} told {helper}.'
    )
    world.events.append(
        f'"Let us replay the sound effects and compare what we hear," {helper} replied.'
    )

    world.events.append(
        f"{detective} placed a fresh record on the phonograph while {helper} watched the shelf."
    )
    world.events.append(
        f"The familiar {p.sound} sounded first. Then came a soft scrape, a pause, and a little click."
    )
    world.events.append(
        f"{helper} noticed that the click happened only when the phonograph's loose lid shut."
    )
    world.events.append(
        f"{detective} lifted the lid and found a narrow hiding space behind the record stack."
    )
    world.events.append(
        f"There was {p.object}, tucked safely behind the phonograph."
    )
    world.events.append(
        f'"I did not take it," admitted {third}. "I hid it so nobody would get it before my turn."'
    )
    world.events.append(
        f'"Thank you for telling the truth," said {detective}. "Next time, ask to share the space."'
    )
    world.events.append(
        f"{third} returned {p.object}, and the group agreed to make a sharing schedule."
    )
    world.events.append(
        f"Afterward, everyone listened together while the phonograph played the same sound effects."
    )
    world.events.append(
        f"The mystery was solved by careful listening, not by a loud accusation."
    )

    world.facts = {
        "detective": detective,
        "helper": helper,
        "suspects": p.suspects,
        "place": p.place,
        "sound": p.sound,
        "object": p.object,
        "culprit": third,
        "method": "hiding the object behind the phonograph's record stack",
        "solution": "replaying the sound effects and noticing the click when the loose lid shut",
        "lesson": "Sharing works best when everyone asks, takes turns, and tells the truth.",
    }
    world.fired.update({"sound_replayed", "clue_found", "object_returned", "sharing_agreed"})
    world.entities["missing_object"].meters["present"] = 1.0
    world.entities["phonograph"].meters["needle_ready"] = 1.0
    world.entities["detective"].memes["reasoning"] = 1.0
    world.entities["helper"].memes["careful_listening"] = 1.0
    world.entities["suspect_3"].memes["honesty"] = 0.8
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params))
    story = " ".join(world.events)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit in {f['place']} involving a phonograph and the missing {f['object']}.",
        f"Use sound effects, careful listening, and sharing to reveal that {f['solution']}.",
        f"Include dialogue between {f['detective']} and {f['helper']} and end with the lesson: {f['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{f['detective']} solved the mystery with help from {f['helper']}.",
        ),
        QAItem(
            question=f"What disappeared from {f['place']}?",
            answer=f"{f['object']} disappeared from {f['place']}.",
        ),
        QAItem(
            question="What clue helped reveal where the missing object was?",
            answer=f"The friends replayed the sound effects and noticed {f['solution']}.",
        ),
        QAItem(
            question="Where was the missing object found?",
            answer=f"It was found {f['method']}.",
        ),
        QAItem(
            question="Who admitted hiding the object?",
            answer=f"{f['culprit']} admitted hiding it so nobody would get it before their turn.",
        ),
        QAItem(
            question="What did the group decide to do afterward?",
            answer="They returned the object and made a sharing schedule so everyone could take turns.",
        ),
        QAItem(
            question="What lesson did the mystery teach?",
            answer=f"The lesson was: {f['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a phonograph?",
            answer="A phonograph is an older machine that plays recorded sound from a record.",
        ),
        QAItem(
            question="Why can sound effects help in a mystery?",
            answer="Sound effects can provide clues when a careful listener notices when, where, or how a sound happens.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means allowing other people to use, enjoy, or receive something fairly.",
        ),
        QAItem(
            question="Why is telling the truth important?",
            answer="Telling the truth helps people understand what happened and repair a problem fairly.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("instrument", "phonograph"),
            asp.fact("value", "sharing"),
            asp.fact("value", "sound_effects"),
            asp.fact("clue", "replayed_sound"),
            asp.fact("resolution", "truth_and_turns"),
        ]
    )


ASP_RULES = r"""
clue_useful(replayed_sound) :- clue(replayed_sound).
fair_resolution(truth_and_turns) :- value(sharing), value(sound_effects).
clue(replayed_sound).
shown_world(phonograph) :- instrument(phonograph).
shown_world(sharing) :- value(sharing).
shown_world(sound_effects) :- value(sound_effects).
#show fair_resolution/1.
#show shown_world/1.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    resolutions = set(asp.atoms(model, "fair_resolution"))
    worlds = set(asp.atoms(model, "shown_world"))
    expected_resolution = {("truth_and_turns",)}
    expected_worlds = {("phonograph",), ("sharing",), ("sound_effects",)}
    if resolutions == expected_resolution and worlds == expected_worlds:
        print("OK: ASP sharing and sound-effects gate matches Python.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP resolutions:", sorted(resolutions))
    print("ASP world facts:", sorted(worlds))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"owner={entity.owner} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
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
        print("== Generation prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(
        detective="Luna",
        helper="Pip",
        suspects=("Mr. Finch", "Mara Mouse", "Grandpa Fox"),
        place="the Moonlit Clubhouse",
        sound="a creaky door",
        object="the brass bell",
        seed=45,
        variant=45,
    ),
    StoryParams(
        detective="Ivy",
        helper="Bea",
        suspects=("Basil Badger", "Cora Crow", "Nell Newt"),
        place="the Lantern Library",
        sound="three tapping spoons",
        object="the silver music box",
        seed=46,
        variant=46,
    ),
]


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


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
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in sorted(map(str, model)):
            print(atom)
        return

    if args.json:
        print(format_json(samples))
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
