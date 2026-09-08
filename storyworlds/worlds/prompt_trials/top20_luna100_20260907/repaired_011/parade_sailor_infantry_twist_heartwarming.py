#!/usr/bin/env python3
"""
A small heartwarming storyworld about a parade, a sailor, and an infantry band.

The town's parade seems ready to begin, but a missing drum strap leaves the
infantry drummer unable to march. A sailor notices the quiet problem, shares a
clever fix, and helps the parade find its true rhythm.
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
    sailor: str
    soldier: str
    friend: str
    town: str
    instrument: str
    twist: int = 0
    opening: int = 0
    heart: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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


CHILDREN = ["Luna", "Milo", "Nia", "Owen", "Pia", "Ravi", "Suki", "Tess"]
SAILORS = ["Sailor Maren", "Sailor Jules", "Sailor Kai", "Sailor Bea"]
SOLDIERS = ["Corporal Reed", "Private Ellis", "Sergeant Moss", "Corporal June"]
FRIENDS = ["Ari", "Ben", "Cleo", "Dara", "Finn", "Jo"]
TOWNS = ["Harborbell", "Sunrise Bay", "Maple Quay", "Bluebell Point"]
INSTRUMENTS = ["snare drum", "brass drum", "parade drum", "little kettle drum"]


OPENINGS = [
    "{child} arrived early in {town}, where flags fluttered above the street for the town parade.",
    "The morning sun shone on {town}'s parade route, and {child} carried a paper flag beside {friend}.",
    "At the harbor end of {town}, families gathered for the parade while bells rang from the boats.",
    "{child} had practiced a parade wave all week. Today, the marching bands were finally coming through {town}.",
    "Colorful banners crossed the street in {town}, and {child} waited to see the sailors and infantry march together.",
    "The parade was meant to thank everyone who cared for the town. {child} and {friend} found a front-row place near the fountain.",
]

TWISTS = [
    {
        "lead": "{soldier} stood with the infantry band, holding a bright {instrument}.",
        "problem": "But the drum strap had snapped, leaving the drum too low to play and the drummer too embarrassed to speak.",
        "risk": "The band was about to march in silence, and the parade captain lifted a hand to start them.",
        "action": "{sailor} noticed the loose strap and said, 'Wait. A sailor knows a knot or two.'",
        "fix": "{sailor} tied a safe bowline with a spare length of clean rope, then asked {child} to test the drum gently.",
        "result": "The drum rested at the right height, and its warm boom rolled down the street.",
        "cause": "the drum strap snapped before the infantry band could march",
        "deed": "noticed the broken strap and helped the sailor test the repair",
        "lesson": "small problems can be solved when someone pays attention",
    },
    {
        "lead": "{soldier} carried the infantry flag while a polished {instrument} waited beside the band.",
        "problem": "A gust lifted the flag's corner and wrapped it around the drumsticks, hiding the first marching beat.",
        "risk": "The parade would begin with the flag tangled and the band unable to see the route.",
        "action": "{child} called, 'The wind is pulling from the harbor!' {sailor} listened and turned the flag toward the calm side of the street.",
        "fix": "{soldier} loosened the cloth while {sailor} clipped a gentle ribbon loop around the pole. The flag waved freely again.",
        "result": "The band could see, the flag streamed like a red sail, and the first beat sounded bright.",
        "cause": "a harbor gust wrapped the infantry flag around the drumsticks",
        "deed": "read the wind and helped the sailor guide the flag to safety",
        "lesson": "careful listening can turn confusion into a clear plan",
    },
    {
        "lead": "The infantry band lined up with a silver {instrument} shining in the sun.",
        "problem": "Just before the parade, {soldier} realized the small music card had blown beneath a bench.",
        "risk": "Without the card, the band might forget the gentle song chosen for the children's hospital.",
        "action": "{child} asked, 'What can we remember?' {sailor} tapped the rhythm on the railing and helped everyone hear the tune.",
        "fix": "The musicians remembered the melody together, and {friend} found the card tucked beneath a fallen scarf.",
        "result": "The band played from memory first, then smiled when the music card returned.",
        "cause": "the wind carried away the infantry band's music card",
        "deed": "asked what the musicians remembered and joined the sailor's steady rhythm",
        "lesson": "shared memories can carry a song even when paper is lost",
    },
    {
        "lead": "{soldier} polished the infantry band's {instrument} until it reflected the parade flags.",
        "problem": "Then a shy child near the curb began to cry because the sudden drumbeat frightened her.",
        "risk": "The parade could pass by without making room for the smallest listener.",
        "action": "{sailor} knelt beside the curb and said, 'We can make the next beat soft.' {child} showed the little girl how to cover her ears.",
        "fix": "{soldier} changed the rhythm to a quiet tap, and the band marched slowly until the child smiled.",
        "result": "When the child waved, the band answered with one gentle boom and a dozen happy grins.",
        "cause": "a loud drumbeat frightened a small child beside the parade route",
        "deed": "helped the sailor comfort the child and made room for a softer rhythm",
        "lesson": "a parade is happiest when everyone has a place in it",
    },
    {
        "lead": "The infantry musicians checked their shoes and lifted the {instrument}.",
        "problem": "A wheel on the parade cart stuck, blocking the street just before the band could move.",
        "risk": "The cart held blankets for the veterans' viewing stand, so leaving it behind would make the celebration feel unfinished.",
        "action": "{child} and {friend} called for help. {sailor} used a smooth wooden peg from a rope crate to lift the wheel.",
        "fix": "{soldier} pushed while the sailor guided the cart, and the wheel rolled freely again.",
        "result": "The blankets reached the stand, and the infantry band followed with a proud, steady rhythm.",
        "cause": "a parade cart wheel stuck across the route",
        "deed": "called for help and helped the sailor move the cart",
        "lesson": "strong work becomes easier when friends share the weight",
    },
    {
        "lead": "{soldier} raised the {instrument} while the infantry band waited beneath the town clock.",
        "problem": "The clock's loud chime covered the first count, and every musician looked uncertainly at the others.",
        "risk": "The parade might begin with scattered steps instead of one proud sound.",
        "action": "{sailor} cupped a hand to the band's leader and called, 'Follow the harbor bell after the echo fades.'",
        "fix": "{child} counted the quiet beats, and {soldier} gave the signal when the street became still.",
        "result": "The band started together, turning the missed count into a strong shared beginning.",
        "cause": "the town clock drowned out the infantry band's starting count",
        "deed": "counted the quiet beats and helped the band find its signal",
        "lesson": "a pause can give people time to find one another",
    },
]

HEARTS = [
    "{child} said, 'You saved the parade.' {sailor} smiled. 'No, we saved it together.' {soldier} added, 'That is how a good crew marches.'",
    "{friend} clapped softly. 'Your knot is clever!' {sailor} replied, 'Clever is useful, but noticing someone who needs help is even better.'",
    "{child} asked, 'Were you worried?' {soldier} answered, 'A little.' {sailor} said, 'That is why we speak up before a little worry grows.'",
    "{sailor} told {child}, 'The sea taught me to trust a careful hand.' {child} answered, 'The parade taught me to use mine for others.'",
    "{soldier} looked at {child}. 'Will you march with us?' {child} said, 'I do not have a uniform.' 'You have a helping heart,' said the soldier. 'That is enough.'",
    "{friend} whispered, 'The parade sounds different now.' {child} replied, 'It sounds like everybody is listening.'",
]

ENDINGS = [
    "At the end of the route, {soldier} let {child} tap the repaired {instrument} once. Its friendly boom made the harbor gulls flutter and the crowd cheer.",
    "The parade stopped beside the veterans' stand. The infantry band played softly for the oldest sailor there, who wiped one bright tear and waved.",
    "{sailor} gave {child} a tiny rope loop as a keepsake. It was not a medal, but {child} wore it proudly because it marked a day of helping.",
    "When the flags came down, {child} saw the repaired gear, the smiling musicians, and {friend}'s waving paper flag. The parade had found its rhythm in kindness.",
    "That evening, {child} taught the family the parade beat. Each person took a turn, and the little room filled with a warm, careful thunder.",
    "The final banner passed beneath the town clock. {child} walked home beside {friend}, hearing the infantry drum echo like a promise that no one had to face trouble alone.",
]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

child_name(N) :- child(N).
sailor_name(S) :- sailor(S).
soldier_name(I) :- soldier(I).
friend_name(F) :- friend(F).
town_name(T) :- town(T).
instrument_name(X) :- instrument(X).

twist_pair(X, T) :- twist_instrument(X, T).
valid(C, S, X) :- child_name(C), sailor_name(S), instrument_name(X), twist_pair(X, T).
valid_story(C, S, X, T) :- valid(C, S, X), town_name(T), soldier_name(I).
"""


TWIST_PAIRS = [
    ("snare drum", "broken strap"),
    ("brass drum", "tangled flag"),
    ("parade drum", "lost music card"),
    ("little kettle drum", "frightened listener"),
]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item in CHILDREN:
        lines.append(asp.fact("child", item))
    for item in SAILORS:
        lines.append(asp.fact("sailor", item))
    for item in SOLDIERS:
        lines.append(asp.fact("soldier", item))
    for item in FRIENDS:
        lines.append(asp.fact("friend", item))
    for item in TOWNS:
        lines.append(asp.fact("town", item))
    for item in INSTRUMENTS:
        lines.append(asp.fact("instrument", item))
    for instrument, twist in TWIST_PAIRS:
        lines.append(asp.fact("twist_instrument", instrument, twist))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return list(TWIST_PAIRS)


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted({(instrument, twist) for _, _, instrument in asp.atoms(model, "valid") for twist in [dict(TWIST_PAIRS).get(instrument)]})


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming parade storyworld.")
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--sailor", choices=SAILORS)
    parser.add_argument("--soldier", choices=SOLDIERS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--town", choices=TOWNS)
    parser.add_argument("--instrument", choices=INSTRUMENTS)
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
    if args.instrument and args.instrument not in INSTRUMENTS:
        raise StoryError("No story: that instrument is not in the parade registry.")
    instrument = args.instrument or rng.choice(INSTRUMENTS)
    return StoryParams(
        child=args.child or rng.choice(CHILDREN),
        sailor=args.sailor or rng.choice(SAILORS),
        soldier=args.soldier or rng.choice(SOLDIERS),
        friend=args.friend or rng.choice(FRIENDS),
        town=args.town or rng.choice(TOWNS),
        instrument=instrument,
        twist=rng.randrange(len(TWISTS)),
        opening=rng.randrange(len(OPENINGS)),
        heart=rng.randrange(len(HEARTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.twist = seed % len(TWISTS)
    params.opening = (seed // len(TWISTS)) % len(OPENINGS)
    params.heart = (seed // 3) % len(HEARTS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    twist = TWISTS[params.twist % len(TWISTS)]
    values = {
        "child": params.child,
        "sailor": params.sailor,
        "soldier": params.soldier,
        "friend": params.friend,
        "town": params.town,
        "instrument": params.instrument,
    }

    world = World()
    child = world.add(Entity(params.child, "character", params.child))
    sailor = world.add(Entity(params.sailor, "character", params.sailor))
    soldier = world.add(Entity(params.soldier, "character", params.soldier))
    drum = world.add(Entity("parade_instrument", "object", params.instrument, {"sound": 0.0}, {"hope": 0.0}))
    route = world.add(Entity("parade_route", "place", params.town, {"crowd": 0.0}, {"belonging": 0.0}))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say(f"{params.sailor} stood near the harbor gate, where a sailor's blue scarf fluttered above the parade crowd.")
    world.say(twist["lead"].format(**values))

    world.para()
    drum.meters["sound"] = 0.2
    route.meters["crowd"] = 1.0
    world.say(twist["problem"].format(**values))
    world.say(twist["risk"].format(**values))
    world.say(twist["action"].format(**values))

    world.para()
    sailor.memes["helpfulness"] = 1.0
    child.memes["courage"] = 1.0
    soldier.memes["relief"] = 1.0
    drum.meters["sound"] = 1.0
    drum.memes["hope"] = 1.0
    route.memes["belonging"] = 1.0
    world.say(twist["fix"].format(**values))
    world.say(twist["result"].format(**values))
    world.say(HEARTS[params.heart % len(HEARTS)].format(**values))
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.child,
        sailor=params.sailor,
        soldier=params.soldier,
        town=params.town,
        instrument=params.instrument,
        parade=True,
        infantry=True,
        twist_cause=twist["cause"],
        helpful_action=twist["deed"],
        resolution=twist["result"],
        lesson=twist["lesson"],
        resolved=True,
    )

    prompts = [
        "Write a heartwarming story about a parade, a sailor, and an infantry band whose small problem is solved through kindness.",
        f"Tell a child-friendly parade story in which {params.child} helps {params.sailor} and {params.soldier} turn a problem into a hopeful ending.",
        f"Write a heartwarming story featuring a {params.instrument}, a sailor's clever help, an infantry parade, and a gentle twist.",
    ]

    story_qa = [
        QAItem(
            question="Who was part of the parade story?",
            answer=f"{params.child} watched and helped {params.sailor} and {params.soldier} during the parade in {params.town}.",
        ),
        QAItem(
            question="What problem interrupted the parade?",
            answer=f"The parade was interrupted because {twist['cause']}.",
        ),
        QAItem(
            question=f"How did {params.child} help?",
            answer=f"{params.child} {twist['deed']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"In the end, {twist['result']}. The parade continued with everyone feeling included and hopeful.",
        ),
        QAItem(
            question="What was the heartwarming lesson?",
            answer=f"The story showed that {twist['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a public procession in which people walk, play music, carry flags, or celebrate together.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or travels by boat and learns practical skills for life near the water.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move mainly on foot.",
        ),
        QAItem(
            question="Why do marching bands use drums?",
            answer="Marching bands use drums to keep a steady beat so people can walk together.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change that makes the story take a new direction.",
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
        lines.append(f"  {entity.id:18} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Sailor Maren", "Corporal Reed", "Ari", "Harborbell", "snare drum", 0, 0, 0, 0),
        StoryParams("Milo", "Sailor Jules", "Private Ellis", "Cleo", "Sunrise Bay", "brass drum", 1, 1, 1, 1),
        StoryParams("Nia", "Sailor Kai", "Sergeant Moss", "Finn", "Maple Quay", "parade drum", 2, 2, 2, 2),
        StoryParams("Owen", "Sailor Bea", "Corporal June", "Dara", "Bluebell Point", "little kettle drum", 3, 3, 3, 3),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible parade instrument and twist pairs:\n")
        for instrument, twist in pairs:
            print(f"  {instrument:20} -> {twist}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("The number of stories must be at least 1.")
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {sample.params.child}: parade in {sample.params.town}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
