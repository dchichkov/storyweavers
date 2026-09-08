#!/usr/bin/env python3
"""
A small animal storyworld about Hbil, bravery, curiosity, and reconciliation.

Hbil is a young forest animal who follows a curious sound, faces a frightening
mistake, and learns that brave listening can mend a friendship.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    helper: str
    object_name: str
    sound: str
    place: str
    incident: int = 0
    premise: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "animal"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Hbil", "Luma", "Niko", "Piri", "Tavi", "Melo"]
FRIENDS = ["Moss", "Kiri", "Bram", "Oona", "Pip", "Sula"]
HELPERS = ["Owl", "Badger", "Tortoise", "Heron", "Fox"]
OBJECTS = ["blue feather", "acorn cup", "silver pebble", "red berry basket"]
SOUNDS = ["a soft tapping", "a tiny bell", "a watery plink", "a rustling hum"]
PLACES = ["the fern meadow", "the moonlit creek", "the old oak grove", "the blackberry hill"]

INCIDENTS = [
    {
        "cause": "Hbil tugged a vine while trying to reach the sound, and the vine pulled a basket from Moss's branch",
        "risk": "The basket swung over the creek, and Moss cried because the berries might fall into the water.",
        "action": "Hbil held the vine steady and called, 'Moss, tell me where to move!' Moss answered, 'Left, then down!'",
        "result": "Hbil followed Moss's directions, and together they lowered the basket onto a flat stone.",
        "repair": "Moss admitted that the basket had been tied too tightly, and Hbil apologized for pulling before asking.",
    },
    {
        "cause": "Hbil's curious paw nudged a pile of leaves and uncovered Kiri's hidden nest",
        "risk": "Kiri fluttered in alarm while the loose leaves began sliding toward the nest.",
        "action": "Hbil froze and said, 'I am sorry. Tell me how to help.' Kiri replied, 'Push the leaves toward the tree root.'",
        "result": "Hbil gently pushed the leaves back, and Kiri tucked the nest safely beneath the root.",
        "repair": "Kiri forgave Hbil after Hbil promised to ask before exploring another animal's hiding place.",
    },
    {
        "cause": "Hbil followed the sound across a log and bumped Bram's carefully balanced pebble tower",
        "risk": "The tower leaned toward Bram, who had spent all morning building it.",
        "action": "Hbil caught one falling pebble and asked, 'Which stone goes first?' Bram pointed to the wide one.",
        "result": "They rebuilt the tower with a wide base, and it stood stronger than before.",
        "repair": "Bram and Hbil agreed that curiosity was welcome when it came with careful feet and kind words.",
    },
    {
        "cause": "Hbil mistook Oona's reed whistle for a strange creature and pulled it from the grass",
        "risk": "The whistle cracked, and Oona's song stopped in the middle of a note.",
        "action": "Hbil carried the pieces back and said, 'I was curious, but I should have asked.' Oona showed Hbil how to mend it.",
        "result": "They tied the reed with a grass ribbon, and the whistle sang a bright little note.",
        "repair": "Oona accepted Hbil's apology, and Hbil waited for permission before touching the next mystery.",
    },
]

PREMISES = [
    "{name} lived near {place}, where every root, feather, and puddle seemed to hide a question.",
    "One morning, {name} promised {friend} to stay on the forest path, but a new sound glittered through the trees.",
    "At sunset, {name} and {friend} were carrying a {object_name} home when curiosity made {name} stop.",
    "The animals of {place} knew {name} as a brave listener, though sometimes curiosity made those listening feet wander.",
]

ENDINGS = [
    "That evening, {name} and {friend} shared the {object_name} beside the quiet path. The sound still seemed mysterious, but their friendship felt clear.",
    "Under the first stars, {name} asked before touching anything, and {friend} answered with a smile. The forest sounded friendly again.",
    "{helper} watched the friends return together. Their careful steps made a tiny trail beside the creek, showing where bravery and forgiveness had walked.",
    "The next day, {name} made a sign that said, 'Look closely, ask kindly.' {friend} helped paint the letters, and both animals laughed at the wobbly final line.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/6.

name(N) :- name_option(N).
friend(F) :- friend_option(F).
helper(H) :- helper_option(H).
object(O) :- object_option(O).
sound(S) :- sound_option(S).
place(P) :- place_option(P).

valid(N, F, P) :- name_option(N), friend_option(F), place_option(P), N != F.
valid_story(N, F, H, O, S, P) :-
    valid(N, F, P),
    helper_option(H),
    object_option(O),
    sound_option(S).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for value in NAMES:
        lines.append(asp.fact("name_option", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend_option", value))
    for value in HELPERS:
        lines.append(asp.fact("helper_option", value))
    for value in OBJECTS:
        lines.append(asp.fact("object_option", value))
    for value in SOUNDS:
        lines.append(asp.fact("sound_option", value))
    for value in PLACES:
        lines.append(asp.fact("place_option", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(name, friend, place) for name in NAMES for friend in FRIENDS for place in PLACES if name != friend]


def asp_valid_combos() -> set[tuple[str, str, str]]:
    import asp

    program = asp_program("#show valid/3.")
    models = asp.solve(program, models=0)
    found: set[tuple[str, str, str]] = set()
    for model in models:
        found.update(tuple(item) for item in asp.atoms(model, "valid"))
    return found


def asp_verify() -> int:
    python_values = set(valid_combos())
    try:
        clingo_values = asp_valid_combos()
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 0
    if python_values == clingo_values:
        print(f"OK: ASP gate matches Python gate ({len(python_values)} combinations).")
        return 0
    print("Mismatch between ASP and Python gates.")
    print("Only in Python:", sorted(python_values - clingo_values))
    print("Only in ASP:", sorted(clingo_values - python_values))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="An animal story about hbil, bravery, curiosity, and reconciliation.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--sound", choices=SOUNDS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    available_friends = [friend for friend in FRIENDS if friend != name]
    friend = args.friend or rng.choice(available_friends)
    if friend == name:
        raise StoryError("Hbil and the friend must be different animals so their reconciliation is meaningful.")
    return StoryParams(
        name=name,
        friend=friend,
        helper=args.helper or rng.choice(HELPERS),
        object_name=args.object_name or rng.choice(OBJECTS),
        sound=args.sound or rng.choice(SOUNDS),
        place=args.place or rng.choice(PLACES),
        incident=rng.randrange(len(INCIDENTS)),
        premise=rng.randrange(len(PREMISES)),
        ending=rng.randrange(len(ENDINGS)),
        seed=None,
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.premise = (seed // len(INCIDENTS)) % len(PREMISES)
    params.ending = (seed // (len(INCIDENTS) * len(PREMISES))) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    values = {
        "name": params.name,
        "friend": params.friend,
        "helper": params.helper,
        "object_name": params.object_name,
        "sound": params.sound,
        "place": params.place,
    }

    world = World()
    protagonist = world.add(Entity(
        id=params.name,
        label=params.name,
        meters={"courage": 0.3, "curiosity": 0.8},
        memes={"worry": 0.2, "trust": 0.5},
    ))
    friend = world.add(Entity(
        id=params.friend,
        label=params.friend,
        meters={"courage": 0.5},
        memes={"hurt": 0.2, "trust": 0.5},
    ))
    helper = world.add(Entity(
        id=params.helper,
        label=params.helper,
        meters={"wisdom": 0.8},
        memes={"patience": 0.8},
    ))
    object_entity = world.add(Entity(
        id="mystery_object",
        kind="thing",
        label=params.object_name,
        meters={"safety": 0.7},
        memes={"meaning": 0.4},
    ))

    world.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    world.say(f"Near the path, {params.sound} came from behind a fern. {params.friend} held the {params.object_name} close and whispered, 'Maybe we should wait for {params.helper.lower()}.'")
    world.say(f"{params.name} answered, 'I am curious, but I will not rush. We can look together.'")

    world.para()
    protagonist.memes["worry"] = 0.7
    object_entity.meters["safety"] = 0.4
    world.say(f"Then {incident['cause']}.")
    world.say(incident["risk"])
    world.say(incident["action"])

    world.para()
    protagonist.meters["courage"] = 1.0
    protagonist.memes["worry"] = 0.1
    friend.memes["hurt"] = 0.0
    friend.memes["trust"] = 0.9
    object_entity.meters["safety"] = 1.0
    object_entity.memes["meaning"] = 0.9
    world.say(incident["result"])
    world.say(incident["repair"])
    world.say(f"{params.helper} nodded and said, 'Bravery is not pretending nothing is scary. It is listening, helping, and making room for forgiveness.'")
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update({
        "protagonist": params.name,
        "friend": params.friend,
        "helper": params.helper,
        "place": params.place,
        "curious_sound": params.sound,
        "object": params.object_name,
        "incident_cause": incident["cause"],
        "helpful_action": incident["action"],
        "resolution": incident["result"],
        "reconciliation": incident["repair"],
        "bravery": True,
        "curiosity": True,
        "resolved": True,
    })

    prompts = [
        "Write an animal story about hbil that uses bravery, curiosity, and reconciliation.",
        f"Tell a child-friendly forest story in which {params.name} follows {params.sound}, makes a mistake with {params.friend}, and repairs the friendship.",
        f"Write a gentle animal adventure featuring {params.name}, {params.friend}, and {params.helper}, with curiosity leading to a brave apology.",
    ]

    story_qa = [
        QAItem(
            question=f"Who is the curious animal in the story?",
            answer=f"{params.name} is the curious animal who follows {params.sound} near {params.place}.",
        ),
        QAItem(
            question="What problem happened?",
            answer=f"The problem happened because {incident['cause']}.",
        ),
        QAItem(
            question=f"How did {params.name} show bravery?",
            answer=f"{params.name} showed bravery by listening carefully, asking how to help, and taking responsibility instead of hiding from the mistake.",
        ),
        QAItem(
            question="How were the friends reconciled?",
            answer=f"They were reconciled when {incident['repair']}",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, the danger was resolved, trust had returned, and curiosity was guided by care and permission.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn about something new or mysterious.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the helpful or right thing even when something feels frightening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement or mistake by listening, apologizing, and rebuilding trust.",
        ),
        QAItem(
            question="Why should animals ask before touching another animal's things?",
            answer="Asking first shows respect and helps keep another animal's nest, food, or special object safe.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:16} ({entity.kind:8}) {' '.join(details)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Hbil", "Moss", "Owl", "blue feather", "a soft tapping", "the fern meadow", 0, 0, 0),
    StoryParams("Luma", "Kiri", "Badger", "acorn cup", "a tiny bell", "the moonlit creek", 1, 1, 1),
    StoryParams("Niko", "Bram", "Tortoise", "silver pebble", "a watery plink", "the old oak grove", 2, 2, 2),
    StoryParams("Piri", "Oona", "Heron", "red berry basket", "a rustling hum", "the blackberry hill", 3, 3, 3),
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
        print(asp_program("#show valid_story/6."))
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        sample = generate(CURATED[0])
        if not sample.story or "Hbil" not in sample.story:
            print("Generated-story verification failed.")
            sys.exit(1)
        print("OK: generated story exercised.")
        return

    if args.asp:
        try:
            combinations = sorted(asp_valid_combos())
        except ImportError as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print(f"{len(combinations)} valid animal/name/place combinations:")
        for name, friend, place in combinations[:40]:
            print(f"  {name} with {friend} at {place}")
        if len(combinations) > 40:
            print(f"  ... and {len(combinations) - 40} more")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for offset in range(max(50, args.n * 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: an animal story of bravery and reconciliation"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
