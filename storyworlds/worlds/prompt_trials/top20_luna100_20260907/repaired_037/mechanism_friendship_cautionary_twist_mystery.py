#!/usr/bin/env python3
"""
A small mystery world about a friendship, a humming mechanism, and a careful
twist: a frightening signal is really a useful repair clue.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    friend_a: str
    friend_b: str
    mechanism: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    warning: int = 0
    reflection: int = 0


SETTINGS = {
    "clocktower": Setting("clocktower", "the old clocktower", {"mechanism", "lantern"}),
    "boathouse": Setting("boathouse", "the quiet boathouse", {"mechanism", "rope"}),
    "workshop": Setting("workshop", "the village workshop", {"mechanism", "tools"}),
}

MECHANISMS = [
    ("brass signal wheel", "a brass wheel clicked behind the wall"),
    ("moon gate", "a little metal gate trembled beneath the window"),
    ("wind-up beacon", "a covered beacon hummed beside the stairs"),
    ("bell-lifting gear", "small gears turned under the floorboards"),
]

NAMES_A = ["Luna", "Mira", "Nell", "Tavi", "Cora", "Iris"]
NAMES_B = ["Pip", "Sol", "Theo", "Jun", "Milo", "Bea"]

INCIDENTS = [
    {
        "clue": "three short clicks, followed by one long scrape",
        "fear": "someone was trapped inside the building",
        "urge": "pull the nearest lever",
        "evidence": "a red thread was caught on the wheel, and dust showed that the lever had not moved in years",
        "truth": "a loose safety cord was winding around the mechanism whenever the night wind entered",
        "repair": "They tied the cord back, cleared the dust from the housing, and tested the wheel with the caretaker.",
        "lesson": "a scary sound deserves a careful question before a daring action",
        "ending": "The repaired wheel turned smoothly, and its small bell welcomed the dawn.",
    },
    {
        "clue": "a blue light blinked twice behind the pipes",
        "fear": "a secret machine was warning them to run",
        "urge": "cover the light with a coat",
        "evidence": "the flashes matched the swing of a loose wire near an old battery",
        "truth": "the beacon was signaling a weak connection, not a hidden danger",
        "repair": "They called the caretaker, who replaced the wire and placed a bright label beside the switch.",
        "lesson": "working together makes a mystery safer to investigate",
        "ending": "The blue beacon shone steadily while the friends walked home shoulder to shoulder.",
    },
    {
        "clue": "a heavy thump came from beneath the stairs",
        "fear": "a giant had stepped into the workshop",
        "urge": "squeeze under the stairs to look",
        "evidence": "a tin cup rolled each time the floorboard lifted, and no footprints crossed the flour dust",
        "truth": "a spring had popped loose and was nudging the cup",
        "repair": "They stayed outside the narrow space while the caretaker secured the spring and moved the cup.",
        "lesson": "friendship means stopping one another when curiosity becomes risky",
        "ending": "The cup rested on a shelf, and the stairs creaked only when someone climbed them.",
    },
    {
        "clue": "a silver pointer spun toward the locked door",
        "fear": "the mechanism was pointing to a hidden treasure room",
        "urge": "force the lock before the pointer stopped",
        "evidence": "the pointer moved whenever the draft slipped under the door",
        "truth": "a bent vane was catching the wind and turning the pointer",
        "repair": "They left the lock untouched, opened a safe window, and asked the caretaker to straighten the vane.",
        "lesson": "a tempting answer is not worth damaging something that belongs to others",
        "ending": "The pointer settled on the quiet window, and the locked door remained unhurt.",
    },
]

OPENINGS = [
    "At twilight, {a} and {b} met beside {place} to return a borrowed lantern.",
    "Rain had just stopped when {a} and {b} slipped along the path to {place}.",
    "The village was settling down for the night, but best friends {a} and {b} had one last errand at {place}.",
    "{a} carried the map while {b} carried the lantern as they entered {place}.",
]

WARNINGS = [
    '"We can investigate without touching anything unknown," said {a}.',
    '"Stay beside me," {b} whispered. "A mystery is not a reason to rush."',
    '"Let us listen first and find an adult if the mechanism is unsafe," said {a}.',
    '"Friends protect each other from brave-looking mistakes," {b} reminded {a}.',
]

REFLECTIONS = [
    '"I nearly made the mystery worse," {a} admitted. "I am glad you stopped me."',
    '"The clue became clearer when we stayed together," said {b}.',
    '"The safest answer was also the real answer," {a} said.',
    '"We did not need to be fearless," {b} decided. "We needed to be careful friends."',
]


ASP_RULES = r"""
#show valid/2.
setting(clocktower). setting(boathouse). setting(workshop).
affords(clocktower,mechanism). affords(clocktower,lantern).
affords(boathouse,mechanism). affords(boathouse,rope).
affords(workshop,mechanism). affords(workshop,tools).
valid(P,A) :- setting(P), affords(P,A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", key, item))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, item) for place, setting in SETTINGS.items() for item in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(python_valid())
    clingo = set(asp_valid())
    if py == clingo:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo - py))
    print("  only in python:", sorted(py - clingo))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    setting = SETTINGS[params.place]
    world = StoryState(setting)
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    mechanism_label, mechanism_sound = MECHANISMS[params.mechanism % len(MECHANISMS)]

    a = world.add(Entity(params.friend_a, "character", "friend", memes={"trust": 1.0}))
    b = world.add(Entity(params.friend_b, "character", "friend", memes={"trust": 1.0}))
    caretaker = world.add(Entity("caretaker", "character", "caretaker"))
    mechanism = world.add(Entity(
        "mechanism", "thing", "mechanism", label=mechanism_label,
        owner="caretaker", meters={"distance_to_path": 2.0, "risk": 0.4},
        memes={"mystery": 1.0},
    ))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        a=a.id, b=b.id, place=setting.place
    ))
    world.say(f"Near the stairs, they heard {incident['clue']}. {mechanism_sound.capitalize()}.")
    world.say(
        f'"Maybe {incident["fear"]}," {a.id} said. '
        f'"Or maybe the sound has an ordinary cause," {b.id} replied.'
    )

    world.para()
    world.say(f"{a.id} wanted to {incident['urge']}.")
    world.say(WARNINGS[params.warning % len(WARNINGS)].format(a=a.id, b=b.id))
    world.say("They kept their hands away from the moving parts and listened from the clear path.")
    world.say(f"Together they noticed that {incident['evidence']}.")
    world.say(REFLECTIONS[params.reflection % len(REFLECTIONS)].format(a=a.id, b=b.id))

    world.para()
    world.say(
        f"The caretaker arrived, and {a.id} explained every clue while {b.id} held the lantern. "
        f'"That was wise," the caretaker said. "{incident["truth"].capitalize()}."'
    )
    world.say(incident["repair"])
    world.say(
        f'"I thought the mystery needed a bold answer," {a.id} told {b.id}. '
        f'"It needed a careful one," {b.id} answered.'
    )
    world.say(f"They smiled because their friendship had changed the plan, and the plan had kept them safe.")
    world.say(incident["ending"])

    world.facts.update(
        friend_a=a,
        friend_b=b,
        caretaker=caretaker,
        mechanism=mechanism,
        incident=incident,
        mechanism_label=mechanism_label,
    )
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly mystery about {f['mechanism_label']} and two friends.",
        f"Tell a cautionary friendship story in which a strange mechanism is investigated safely.",
        "Write a mystery with dialogue, a misleading first guess, a useful clue, and a peaceful twist.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    a, b, incident = f["friend_a"], f["friend_b"], f["incident"]
    return [
        QAItem(
            "Who investigated the mysterious mechanism?",
            f"{a.id} and {b.id} investigated it together, protecting one another as friends.",
        ),
        QAItem(
            f"What did {a.id} first want to do?",
            f"{a.id} wanted to {incident['urge']}, but {b.id} urged caution so nobody would be hurt.",
        ),
        QAItem(
            "What clue changed their understanding?",
            f"They noticed that {incident['evidence']}. That clue pointed away from the frightening first guess.",
        ),
        QAItem(
            "What was the true cause of the mystery?",
            f"The true cause was that {incident['truth']}.",
        ),
        QAItem(
            "How did friendship help?",
            f"The friends shared observations and stopped each other from taking a risky action, so the mechanism could be repaired safely.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            "What is a mechanism?",
            "A mechanism is a group of moving parts that works together to do a job.",
        ),
        QAItem(
            "Why should children avoid unknown moving machines?",
            "Unknown machines may pinch, cut, or start unexpectedly, so children should keep clear and ask a trusted adult for help.",
        ),
        QAItem(
            "What makes a good friend during a mystery?",
            "A good friend listens, shares clues, and speaks up when a plan could be unsafe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    friend_a = args.friend_a or rng.choice(NAMES_A)
    friend_b = args.friend_b or rng.choice(NAMES_B)
    if friend_a == friend_b:
        choices = [name for name in NAMES_B if name != friend_a]
        friend_b = rng.choice(choices)
    mechanism = args.mechanism if args.mechanism is not None else rng.randrange(len(MECHANISMS))
    if not 0 <= mechanism < len(MECHANISMS):
        raise StoryError("Mechanism index must refer to a registered mechanism.")
    return StoryParams(
        place=place,
        friend_a=friend_a,
        friend_b=friend_b,
        mechanism=mechanism,
        seed=None,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        warning=rng.randrange(len(WARNINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
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
        description="Mystery storyworld about friendship, caution, and a mechanism."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--friend-a")
    parser.add_argument("--friend-b")
    parser.add_argument("--mechanism", type=int, choices=range(len(MECHANISMS)))
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        rows = asp_valid()
        print(f"{len(rows)} valid combinations:\n")
        for place, item in rows:
            print(f"  {place:12} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(
                place=place,
                friend_a="Luna",
                friend_b="Pip",
                mechanism=0,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target and attempt < max(50, target * 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
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
