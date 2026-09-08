#!/usr/bin/env python3
"""
A small mystery world about a clockwork bridge, friendship, caution, and a twist.
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
    hero_name: str
    friend_name: str
    seed: Optional[int] = None
    incident: int = 0
    opening: int = 0
    warning: int = 0
    turn: int = 0
    ending: int = 0


SETTINGS = {
    "clocktower": Setting("the old clocktower", {"mechanism", "bridge"}),
    "workshop": Setting("the village workshop", {"mechanism", "tools"}),
    "riverbank": Setting("the riverbank clock house", {"mechanism", "bridge"}),
}

HERO_NAMES = ["Luna", "Mira", "Tess", "Nell", "Iris", "Pia"]
FRIEND_NAMES = ["Oren", "Bram", "Finn", "Jo", "Sol", "Kit"]

INCIDENTS = [
    {
        "clue": "three brass teeth turning inside a locked wooden box",
        "guess": "someone had hidden a tiny machine in the tower",
        "danger": "put a finger through the opening to stop the spinning teeth",
        "sound": "a deep click echoed below the floor",
        "evidence": "the teeth turned only when the tower bell rope swayed",
        "test": "They marked the rope with chalk, stepped back, and watched the mechanism complete one slow circle.",
        "truth": "the bell rope was pulling the clock's winding mechanism",
        "repair": "They tied the rope safely aside and told the clock keeper what they had found.",
        "lesson": "a curious hand should wait when a moving mechanism is not understood",
        "ending": "At sunset, the repaired clock ticked steadily above the two friends.",
    },
    {
        "clue": "a silver lever trembling beside the bridge gate",
        "guess": "a hidden watchman was signaling from inside the gate",
        "danger": "pull the lever before the river carried the signal away",
        "sound": "the gate groaned, though nobody stood nearby",
        "evidence": "water drops marked the lever, and the bridge chain moved with each river surge",
        "test": "They stayed on the stone path and counted the chain's movement instead of touching the lever.",
        "truth": "a water wheel was driving the bridge mechanism",
        "repair": "They placed a warning sign by the wet stones and fetched the bridge keeper.",
        "lesson": "a mystery near water deserves extra care before anyone reaches for a lever",
        "ending": "The bridge opened smoothly while Luna and her friend watched from dry ground.",
    },
    {
        "clue": "a red light blinking beneath a workbench",
        "guess": "a secret messenger had left a warning inside the workshop",
        "danger": "crawl under the bench and grab the blinking object",
        "sound": "a small wheel rattled whenever they whispered",
        "evidence": "the light blinked beside a loose spring and stopped when the bench was still",
        "test": "They used a ruler to point from a distance and asked the maker for permission before moving anything.",
        "truth": "the light belonged to a wind-up signal mechanism with a loose spring",
        "repair": "The maker secured the spring and gave them a safe demonstration of the signal.",
        "lesson": "asking for help can reveal a mechanism without turning a puzzle into a danger",
        "ending": "The red signal blinked only when invited, like a polite little star.",
    },
    {
        "clue": "a trail of fresh copper dust leading behind the clock face",
        "guess": "a hidden thief had scraped a message into the gears",
        "danger": "squeeze behind the clock face to follow the trail",
        "sound": "the minute hand skipped with a sharp metallic snap",
        "evidence": "the dust ended at a loose gear, and the clock lost one minute each hour",
        "test": "They blocked the narrow door, wrote down the time, and waited for the keeper.",
        "truth": "one worn gear was shaving itself as it turned",
        "repair": "The keeper replaced the gear and swept the copper dust into a small tin.",
        "lesson": "a quiet record and a patient wait can solve a mystery more safely than a chase",
        "ending": "The minute hand kept perfect time, and the copper dust stayed sealed in its tin.",
    },
]

OPENINGS = [
    "Luna and {friend} were crossing {place} when they noticed something that did not belong.",
    "A gray afternoon wrapped around {place}, and Luna met {friend} there to solve a small mystery.",
    "The first bell had not rung at {place}. Luna and {friend} came closer, listening carefully.",
    "While everyone else hurried home, Luna and {friend} paused beside {place}.",
]

WARNINGS = [
    '"Do not touch it yet," Luna said. "A moving part can surprise us."',
    '"Mysteries are not invitations to grab," said Luna. "Let us look from here first."',
    '"We can be brave and careful together," {friend} replied. "Who should we ask?"',
    '"First we learn what makes it move," Luna said. "Then we choose what to do."',
]

TURNS = [
    "They marked the safe place with a pebble and watched without stepping closer.",
    "Their first guess felt exciting, but the ordinary clues were stronger.",
    "The friends compared what each of them had seen instead of arguing about the answer.",
    "Together they followed the sound only as far as the clear, dry path.",
]

ENDINGS = [
    '"I thought solving meant acting fast," {friend} said. "Now I think it means noticing more."',
    '"Good friends do not push each other toward danger," Luna replied. "They help each other pause."',
    '"The mechanism was mysterious," said {friend}, "but our careful plan made it understandable."',
    '"We solved it because we stayed together," Luna said, smiling as the machine settled down.',
]


ASP_RULES = r"""
#show valid/2.
setting(clocktower). setting(workshop). setting(riverbank).
affords(clocktower,mechanism). affords(clocktower,bridge).
affords(workshop,mechanism). affords(workshop,tools).
affords(riverbank,mechanism). affords(riverbank,bridge).
valid(P,A) :- setting(P), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", place, affordance))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple[str, str]]:
    return sorted((place, thing) for place, setting in SETTINGS.items() for thing in setting.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = set(python_valid())
    actual = set(asp_valid())
    if expected == actual:
        print(f"OK: clingo gate matches python gate ({len(expected)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(actual - expected))
    print("  only in python:", sorted(expected - actual))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero_name == params.friend_name:
        raise StoryError("Hero and friend must have different names.")

    setting = SETTINGS[params.place]
    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    world = StoryState(setting)
    hero = world.add(Entity(params.hero_name, "character", "friend", memes={"caution": 0.8}))
    friend = world.add(Entity(params.friend_name, "character", "friend", memes={"trust": 0.7}))
    mechanism = world.add(Entity("mechanism", "thing", "mechanism", label="the strange mechanism",
                                 owner="clockkeeper", meters={"moving_parts": 1.0}))
    world.add(Entity("clockkeeper", "character", "helper"))

    place = setting.place
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(place=place, friend=friend.id))
    world.say(f"They saw {incident['clue']}.")
    world.say(f'"Maybe {incident["guess"]}," said {hero.id}. "{incident["guess"].capitalize()}," {friend.id} whispered.')
    world.para()
    world.say(f"Then {incident['sound']}. {friend.id} wanted to {incident['danger']}.")
    world.say(WARNINGS[params.warning % len(WARNINGS)].format(friend=friend.id))
    world.say(TURNS[params.turn % len(TURNS)])
    world.say(f"From the safe path, they noticed that {incident['evidence']}.")
    world.say(incident["test"])
    world.para()
    world.say(f"The clockkeeper arrived. {hero.id} explained every clue, and {friend.id} showed the chalk mark.")
    world.say(f'"The twist is that {incident["truth"]}," said the clockkeeper.')
    world.say(incident["repair"])
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(friend=friend.id))
    world.say(f"The friends left {place} together, proud that caution had protected their friendship.")
    world.say(incident["ending"])
    world.facts.update(hero=hero, friend=friend, mechanism=mechanism, incident=incident, place=place)
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a mystery story about {f['hero'].id} and {f['friend'].id} investigating a mechanism at {f['place']}.",
        "Tell a cautionary friendship story where careful observation reveals a surprising twist.",
        "Write a child-friendly mystery with dialogue, a moving mechanism, teamwork, and a peaceful ending.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    return [
        QAItem("Who investigated the mystery?", f"{f['hero'].id} and {f['friend'].id} investigated it together and stayed close to the safe path."),
        QAItem("What did the friend first want to do?", f"{f['friend'].id} wanted to {incident['danger']}, but the friends decided to observe before touching anything."),
        QAItem("What clue changed their understanding?", f"They noticed that {incident['evidence']}. This showed that {incident['truth']}."),
        QAItem("How did caution protect the friends?", "They kept away from the moving parts, recorded clues, and asked the clockkeeper for help."),
        QAItem("What happened at the end?", incident["repair"] + " " + incident["ending"]),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem("What is a mechanism?", "A mechanism is a group of moving parts that works together to do a job."),
        QAItem("Why should people be careful around moving parts?", "Moving parts can pinch, catch, or surprise someone, so it is safer to keep a distance and ask a trusted adult for help."),
        QAItem("How can friendship help during a mystery?", "Friends can share clues, remind each other to be cautious, and make better decisions together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        lines.append(f"  {entity.id:12} ({entity.type}) meters={entity.meters} memes={entity.memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    return StoryParams(
        place=place,
        hero_name=hero,
        friend_name=friend,
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        warning=rng.randrange(len(WARNINGS)),
        turn=rng.randrange(len(TURNS)),
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
        print("\n" + format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mystery world of mechanisms, friendship, caution, and a twist.")
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("\n".join(f"{place:12} {thing}" for place, thing in asp_valid()))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for place in SETTINGS:
            samples.append(generate(StoryParams(place, "Luna", "Oren")))
    else:
        seen = set()
        for i in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(seed + i)
            params = resolve_params(args, rng)
            params.seed = seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
