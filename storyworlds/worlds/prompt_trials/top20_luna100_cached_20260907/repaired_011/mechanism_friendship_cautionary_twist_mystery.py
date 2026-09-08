#!/usr/bin/env python3
"""
A small mystery storyworld about a curious mechanism, friendship, and a careful twist.

A child and a friend discover a strange clicking device in an old shed. Their
friendship helps them investigate, but a cautionary clue teaches them not to
touch an unknown mechanism before understanding what it does.
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
class StoryParams:
    child: str
    friend: str
    object_name: str
    clue: str
    caretaker: str
    incident: int = 0
    opening: int = 0
    twist: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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


CHILDREN = ["Mara", "Leo", "Nia", "Tomas", "Ivy", "Sam", "Owen", "Zara"]
FRIENDS = ["Pip", "June", "Rafi", "Bea", "Milo", "Tess", "Kai", "Wren"]
OBJECTS = [
    "brass box",
    "wind-up bird",
    "wooden dial",
    "silver music wheel",
    "stone counter",
    "copper key machine",
]
CLUES = [
    "three blue scratches",
    "a faded star",
    "a red thread",
    "a row of tiny moons",
    "a green glass bead",
    "a paper arrow",
]
CARETAKERS = ["Grandma Jo", "Mr. Vale", "Aunt Rue", "Uncle Ben", "Ms. Clover"]

MECHANISM_PAIRS = [
    ("brass box", "three blue scratches"),
    ("wind-up bird", "a faded star"),
    ("wooden dial", "a red thread"),
    ("silver music wheel", "a row of tiny moons"),
    ("stone counter", "a green glass bead"),
    ("copper key machine", "a paper arrow"),
]

OPENINGS = [
    "{child} and {friend} were sorting dusty jars in the garden shed when a soft click came from beneath a folded canvas.",
    "Rain kept {child} and {friend} indoors, so they explored the old workshop beside {caretaker}'s house.",
    "{child} promised {friend} they would solve one small mystery before lunch. The promise began when a hidden gear ticked in the wall.",
    "At the edge of the orchard, {child} and {friend} found a narrow door that neither of them remembered seeing before.",
    "{friend} noticed a thin line of light under a workbench. {child} knelt beside it, and something inside clicked twice.",
    "The shed had been quiet for years, but that morning a tiny rhythm came from its locked cabinet."
]

INCIDENTS = [
    {
        "lead": "{child} pulled away the canvas and found the {object_name}, marked with {clue}.",
        "trigger": "When {friend} leaned close, the mechanism clicked faster and a little metal arm pointed toward a loose floorboard.",
        "risk": "The board trembled, and both friends wondered whether the device was opening a trap or merely showing a secret.",
        "action": "{child} said, 'Let's not turn anything yet.' {friend} placed a ruler beside the arm and watched its movement without touching the gears.",
        "resolution": "The ruler showed that the arm moved only when a draft came through a crack. Beneath the floorboard they found a safe message, not a trap.",
        "cause": "the mechanism reacted to a draft and pointed at a loose floorboard",
        "deed": "suggested observing the device instead of turning it",
        "result": "the friends discovered that the device was a wind-powered pointer",
    },
    {
        "lead": "The {object_name} sat in a nest of dust, and {clue} was painted beside its small brass lever.",
        "trigger": "A tap from the rain made the lever jump. Somewhere behind the wall, a bell gave one lonely ring.",
        "risk": "The bell might have called someone, released something, or warned that the old machine was waking.",
        "action": "{friend} whispered, 'We can listen first.' {child} marked the lever's position with a pebble and fetched {caretaker}.",
        "resolution": "{caretaker} opened the back panel and revealed a harmless bell connected to the rain barrel's overflow.",
        "cause": "rain made the lever move and ring a hidden bell",
        "deed": "marked the lever and asked a trusted adult for help",
        "result": "the adult showed that the bell warned about a full rain barrel",
    },
    {
        "lead": "{child} found the {object_name} inside a wooden drawer, with {clue} scratched across its lid.",
        "trigger": "The drawer slid shut by itself, and a row of tiny windows changed from dark to gold.",
        "risk": "The changing lights made the friends fear that the box had started a countdown.",
        "action": "{child} and {friend} stepped back. They sketched the windows and searched the drawer for instructions instead of forcing it open.",
        "resolution": "The sketch matched a sunrise chart hidden under the lining. The golden windows were simply a weather-and-light display.",
        "cause": "the drawer closed and the mechanism's windows lit up",
        "deed": "stepped back and searched for instructions rather than forcing the drawer",
        "result": "the friends learned that the windows displayed daylight changes",
    },
    {
        "lead": "Behind a stack of jars, {friend} spotted the {object_name} carrying the mark of {clue}.",
        "trigger": "A loose cord tugged the machine, and its pointer swung toward a dark corner where something scraped.",
        "risk": "The scrape sounded like footsteps, though no one else was supposed to be in the shed.",
        "action": "{friend} held {child}'s hand. Together they called, 'Is anyone there?' and waited before moving closer.",
        "resolution": "A hedgehog shuffled out from behind the boxes, dragging the cord that powered the pointer.",
        "cause": "a loose cord made the pointer swing while an animal moved nearby",
        "deed": "called out and waited instead of rushing into the dark corner",
        "result": "the friends found a hedgehog causing the mysterious scraping",
    },
    {
        "lead": "{child} discovered the {object_name} under a cloth, with {clue} sewn into its cover.",
        "trigger": "The cloth slipped, revealing a keyhole. Before anyone touched it, the machine began making a slow clicking pattern.",
        "risk": "The pattern sounded like a code, but guessing at a code could start the wrong part of the machine.",
        "action": "{friend} counted the clicks while {child} compared them with marks on the cloth. They waited until the pattern stopped.",
        "resolution": "The clicks matched the safe-release symbol. When {caretaker} used the proper key, a drawer opened with a friendship note inside.",
        "cause": "the hidden keyhole and clicking pattern suggested a coded release",
        "deed": "counted the clicks and waited for the pattern to stop",
        "result": "the proper key opened a drawer containing a friendship note",
    },
    {
        "lead": "In the corner stood the {object_name}, labeled with {clue} and covered in cobwebs.",
        "trigger": "A tiny wheel began turning after sunlight crossed the window, and a painted arrow pointed at the friends' basket.",
        "risk": "The basket held their snacks, and the arrow made it seem as if the machine wanted something from them.",
        "action": "{child} said, 'We should understand the arrow before we obey it.' {friend} checked the basket without moving the machine.",
        "resolution": "A mirror inside the device had caught the sunlight and pointed at a shiny lunch tin. The strange request was only a reflection.",
        "cause": "sunlight turned a wheel and a mirror pointed toward a shiny lunch tin",
        "deed": "checked the clue without obeying the unexplained signal",
        "result": "the friends traced the signal to sunlight and a mirror",
    },
]

TWISTS = [
    "'The mystery is not what the machine wants,' said {friend}. 'It is what makes it move.' {child} agreed, and they began looking for causes instead of guesses.",
    "{child} said, 'A scary sound is still only a sound until we learn its source.' That careful idea changed the search from a chase into an investigation.",
    "{friend} grinned. 'Maybe the secret is a safety lesson wearing a mystery costume.' The hidden message proved that friendship and patience were part of the design.",
    "The strangest clue was the one they had almost missed: a note saying, 'Good helpers wait.' The machine had been built to reward careful eyes.",
    "'We solved it together,' said {child}. 'You noticed the clue, and I noticed the pattern.' Their discovery felt better because neither friend had rushed alone.",
    "The device had never been trying to frighten them. It had been waiting for someone to notice the ordinary cause behind the unusual clue."
]

ENDINGS = [
    "{caretaker} placed the harmless mechanism on a shelf with a new label: LOOK, LISTEN, THEN TOUCH. {child} and {friend} added their names beneath it.",
    "Before leaving, the friends tied a bright ribbon near the machine. The ribbon moved in the same draft that had set the pointer clicking.",
    "The rain stopped, and the shed filled with warm light. On the workbench, the friends' careful sketch rested beside the solved mechanism.",
    "{child} and {friend} shared their snacks beside the quiet device. Every few moments it clicked, and now the sound felt like a friendly hello.",
    "{caretaker} let the friends keep the safe message. They folded it into a notebook where every mystery began with a question, not a grab.",
    "That evening, {friend} drew the machine with a smiling face. Underneath, {child} wrote, 'A true mystery becomes clearer when friends slow down together.'"
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

child_name(X) :- child(X).
friend_name(X) :- friend(X).
object_name(X) :- object(X).
clue_name(X) :- clue(X).
caretaker_name(X) :- caretaker(X).

mechanism_pair(O, C) :- pair(O, C).
valid(C, F, O) :- child_name(C), friend_name(F), mechanism_pair(O, _).
valid_story(C, F, O, K) :- valid(C, F, O), caretaker_name(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for value in CHILDREN:
        lines.append(asp.fact("child", value))
    for value in FRIENDS:
        lines.append(asp.fact("friend", value))
    for value in OBJECTS:
        lines.append(asp.fact("object", value))
    for value in CLUES:
        lines.append(asp.fact("clue", value))
    for value in CARETAKERS:
        lines.append(asp.fact("caretaker", value))
    for obj, clue in MECHANISM_PAIRS:
        lines.append(asp.fact("pair", obj, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return list(MECHANISM_PAIRS)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mechanism_pair/2."))
    return sorted(asp.atoms(model, "mechanism_pair"))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches mechanism pairs ({len(py)} pairs).")
        return 0
    print("MISMATCH between Python and ASP mechanism pairs.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about a mechanism, friendship, and caution."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--caretaker", choices=CARETAKERS)
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
    pairs = valid_combos()
    if args.object_name and args.clue:
        if (args.object_name, args.clue) not in pairs:
            raise StoryError(
                "No valid mystery: that mechanism and clue do not belong to the same careful investigation."
            )
    if args.object_name:
        pairs = [pair for pair in pairs if pair[0] == args.object_name]
    if args.clue:
        pairs = [pair for pair in pairs if pair[1] == args.clue]
    if not pairs:
        raise StoryError("No mechanism-and-clue pair matches the requested options.")
    object_name, clue = rng.choice(sorted(pairs))
    child = args.child or rng.choice(CHILDREN)
    friend = args.friend or rng.choice([name for name in FRIENDS if name != child])
    return StoryParams(
        child=child,
        friend=friend,
        object_name=object_name,
        clue=clue,
        caretaker=args.caretaker or rng.choice(CARETAKERS),
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.opening = (seed // len(INCIDENTS)) % len(OPENINGS)
    params.twist = (seed // 3) % len(TWISTS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    if (params.object_name, params.clue) not in valid_combos():
        raise StoryError("The selected mechanism and clue do not form a supported mystery.")

    values = {
        "child": params.child,
        "friend": params.friend,
        "object_name": params.object_name,
        "clue": params.clue,
        "caretaker": params.caretaker,
    }
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            label=params.child,
            memes={"curiosity": 0.2, "caution": 0.1, "trust": 0.5},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            label=params.friend,
            memes={"curiosity": 0.3, "caution": 0.2, "trust": 0.5},
        )
    )
    caretaker = world.add(
        Entity(
            id="caretaker",
            kind="character",
            label=params.caretaker,
            memes={"trust": 0.8},
        )
    )
    mechanism = world.add(
        Entity(
            id="mechanism",
            label=params.object_name,
            meters={"motion": 0.0, "risk": 0.0},
            memes={"mystery": 0.8, "understanding": 0.0},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            label=params.clue,
            meters={"visibility": 0.5},
            memes={"meaning": 0.0},
        )
    )

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say(incident["lead"].format(**values))
    world.say(
        f"The {params.object_name} looked old but carefully made. {params.child} and {params.friend} "
        f"had the same thought: a mystery was exciting, but an unknown mechanism deserved respect."
    )

    world.para()
    mechanism.meters["motion"] = 1.0
    mechanism.meters["risk"] = 0.6
    mechanism.memes["mystery"] = 1.0
    child.memes["curiosity"] = 0.9
    friend.memes["caution"] = 0.8
    world.say(incident["trigger"].format(**values))
    world.say(incident["risk"].format(**values))
    world.say(incident["action"].format(**values))

    world.para()
    mechanism.meters["risk"] = 0.0
    mechanism.memes["understanding"] = 1.0
    clue.memes["meaning"] = 1.0
    child.memes["caution"] = 1.0
    friend.memes["trust"] = 1.0
    caretaker.memes["pride"] = 1.0
    world.say(incident["resolution"].format(**values))
    world.say(TWISTS[params.twist % len(TWISTS)].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.child,
        friend=params.friend,
        caretaker=params.caretaker,
        mechanism=params.object_name,
        clue=params.clue,
        mystery_cause=incident["cause"],
        careful_action=incident["deed"],
        resolution=incident["result"],
        friendship=True,
        cautionary=True,
        twist=True,
        resolved=True,
    )

    prompts = [
        "Write a child-friendly mystery about friends discovering an unknown mechanism and solving it cautiously.",
        f"Tell a mystery in which {params.child} and {params.friend} investigate a {params.object_name} marked with {params.clue}.",
        f"Write a friendship story with a cautionary twist: the children should observe the mechanism before touching it.",
    ]

    story_qa = [
        QAItem(
            question="Who investigated the mysterious mechanism?",
            answer=f"{params.child} and {params.friend} investigated it together, using friendship and patience instead of rushing.",
        ),
        QAItem(
            question="What made the discovery feel mysterious?",
            answer=f"The discovery felt mysterious because {incident['cause']}. The unusual clue made the friends wonder what the mechanism did.",
        ),
        QAItem(
            question=f"What did {params.child} and {params.friend} do carefully?",
            answer=f"They {incident['deed']}. Their careful choice kept the investigation safe and helped them learn the truth.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {incident['result']}. The strange event had an ordinary explanation once the friends studied it.",
        ),
        QAItem(
            question="How did friendship help?",
            answer=f"They shared observations, listened to each other, and made decisions together, so neither friend had to face the mystery alone.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, change, or perform a task.",
        ),
        QAItem(
            question="Why should people be cautious with unknown machines?",
            answer="People should be cautious because an unknown machine may have moving parts, sharp edges, heat, or a purpose they do not understand.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question or puzzling event whose answer must be discovered by noticing clues and testing ideas.",
        ),
        QAItem(
            question="How can friends solve a problem together?",
            answer="Friends can share what they notice, listen to different ideas, and choose a safe plan together.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in understanding that makes earlier clues fit in a new way.",
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
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:11} ({entity.kind:9}) {' '.join(bits)}")
    if world.facts:
        lines.append(f"  facts       {world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            child="Mara",
            friend="Pip",
            object_name="brass box",
            clue="three blue scratches",
            caretaker="Grandma Jo",
            incident=0,
            opening=0,
            twist=0,
            ending=0,
        ),
        StoryParams(
            child="Leo",
            friend="June",
            object_name="wind-up bird",
            clue="a faded star",
            caretaker="Mr. Vale",
            incident=3,
            opening=2,
            twist=2,
            ending=2,
        ),
        StoryParams(
            child="Nia",
            friend="Rafi",
            object_name="wooden dial",
            clue="a red thread",
            caretaker="Aunt Rue",
            incident=4,
            opening=4,
            twist=4,
            ending=4,
        ),
        StoryParams(
            child="Ivy",
            friend="Bea",
            object_name="silver music wheel",
            clue="a row of tiny moons",
            caretaker="Ms. Clover",
            incident=5,
            opening=5,
            twist=5,
            ending=5,
        ),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid/3.\n#show valid_story/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible mechanism-and-clue pairs:\n")
        for object_name, clue in pairs:
            print(f"  {object_name:20} -> {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"### {params.child}: the {params.object_name} "
                f"and {params.clue}"
            )
        elif len(samples) > 1:
            header = f"### mystery variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
