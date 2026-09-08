#!/usr/bin/env python3
"""
A child-friendly mystery about a curious mechanism, a friendship, and a warning
that turns out to hide a kinder truth.
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
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    friend_name: str = "Milo"
    place: str = "the old clock house"
    object_name: str = "the brass moon machine"


NAMES = ["Luna", "Milo", "Iris", "Theo", "Nia", "Owen", "Pia", "Sam"]
PLACES = ["the old clock house", "the locked garden shed", "the quiet train station", "the lighthouse workshop"]
OBJECTS = ["the brass moon machine", "the silver bird mechanism", "the wooden rain wheel", "the tiny star projector"]

CASES = [
    {
        "title": "the whispering brass moon",
        "mechanism": "a brass mechanism with three moon-shaped gears",
        "warning": "Never wind the smallest gear after sunset",
        "clue": "a thread of blue dust under the smallest gear",
        "wrong": "wound the largest gear too quickly and made the moon-shaped gears jam",
        "setback": "the machine's roof window stayed dark during the town's night walk",
        "method": "they brushed away the blue dust, counted the teeth on each gear, and turned the smallest gear only when the bell rang",
        "twist": "the warning was not meant to keep children away; it protected a hidden nest of glow-moths that slept inside the moon housing",
        "ending": "the repaired machine opened the roof, and gentle moth-light floated over the friends like tiny moons",
        "lesson": "A warning deserves careful listening before it deserves a brave experiment",
    },
    {
        "title": "the clockwork garden gate",
        "mechanism": "a green mechanism of springs, pins, and a flower-shaped handle",
        "warning": "Do not pull the flower before the gate sings",
        "clue": "three fresh scratches beside the silent music pins",
        "wrong": "pulled the flower handle before checking the pins and locked the gate tighter",
        "setback": "their basket of seedlings stayed outside the garden during the hottest part of the day",
        "method": "they matched each pin to a colored leaf, listened for the little tune, and pulled the handle together",
        "twist": "the warning protected a shy hedgehog family that slept beneath the gate until the song woke them safely",
        "ending": "the gate opened without a clank, and the seedlings stood fresh in their new beds",
        "lesson": "A mechanism may be guarding something small and living, not hiding a treasure",
    },
    {
        "title": "the station's backward clock",
        "mechanism": "a round mechanism whose hands moved through a nest of tiny cogs",
        "warning": "Never set the red hand straight",
        "clue": "a folded timetable tucked behind the clock face",
        "wrong": "forced the red hand straight and stopped every clock in the station",
        "setback": "the evening train could not receive its platform signal",
        "method": "they read the timetable, turned the hands backward one minute at a time, and tested the bell after each turn",
        "twist": "the warning hid a safety rule: the red hand had to point slightly aside so birds would not mistake it for a bright perch",
        "ending": "the station bell rang, the train found its platform, and a flock of sparrows flew safely past",
        "lesson": "A strange rule can make sense when you discover whom it protects",
    },
    {
        "title": "the lighthouse riddle",
        "mechanism": "a glass-and-copper mechanism that turned the lighthouse beam",
        "warning": "Do not polish the dark lens",
        "clue": "salt crystals arranged in an arrow on the floor",
        "wrong": "polished the dark lens until the beam spun in the wrong direction",
        "setback": "the fishing boats saw a confusing flash and waited outside the harbor",
        "method": "they followed the salt arrow, loosened the lens ring, and cleaned only the bright glass",
        "twist": "the dark lens was a shadow marker showing where the beam must pause for boats carrying sleeping babies",
        "ending": "the beam swept in a calm rhythm, guiding every boat into the harbor",
        "lesson": "Not every dark part is broken; some parts make the whole design safe",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(params.child_name, "character", "child", params.child_name))
    friend = world.add(Entity(params.friend_name, "character", "child", params.friend_name))
    machine = world.add(Entity("mechanism", "thing", "mechanism", params.object_name))
    clue = world.add(Entity("clue", "thing", "clue", "mysterious clue"))
    place = world.add(Entity("place", "place", "setting", params.place))

    child.meters.update(courage=1.0, care=0.7)
    friend.meters.update(observation=1.0, care=0.8)
    machine.meters.update(order=1.0, danger=0.0)
    machine.memes["mystery"] = 1.0
    clue.meters["evidence"] = 1.0
    place.memes["secrecy"] = 1.0
    world.facts.update(child=child, friend=friend, machine=machine, clue=clue, place=place)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.child_name}|{params.friend_name}|{params.place}|{params.object_name}"
    ))


def valid_story() -> bool:
    return True


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    case = CASES[_token(params) % len(CASES)]
    child = world.facts["child"]
    friend = world.facts["friend"]
    machine = world.facts["machine"]
    clue = world.facts["clue"]

    world.say(f"{child.label} and {friend.label} visited {params.place} to investigate {case['mechanism']}.")
    world.say(f"A faded card beside it carried one warning: “{case['warning']}”")
    world.say(f"The warning made the mechanism seem mysterious, but the friends promised to stay together and touch nothing until they understood it.")

    world.para()
    world.say(f"{child.label} pointed to a loose lever. “Maybe this starts it,” {child.label} said.")
    world.say(f"“Wait,” {friend.label} replied. “A warning is a clue, not a challenge.”")
    world.say(f"They looked more closely and found {case['clue']}.")
    world.say(f"Before they could agree, {child.label} {case['wrong']}.")

    machine.meters["danger"] = 1.0
    machine.meters["order"] = 0.0
    world.fired.add(("wrong_choice",))
    world.say(f"The result was disappointing: {case['setback']}.")
    world.say(f"{friend.label} held the stuck handle. “We made the mystery worse,” {friend.label} said.")
    world.say(f"{child.label} took a breath. “Then we will repair it carefully, together.”")

    world.para()
    world.say(f"They examined the mechanism instead of guessing. The clue became useful when {case['method']}.")
    world.say(f"“The warning was trying to tell us something,” {child.label} said.")
    world.say(f"“Yes,” {friend.label} answered. “And the something is smaller and kinder than we expected.”")
    world.say(f"That was the twist: {case['twist']}")

    machine.meters["danger"] = 0.0
    machine.meters["order"] = 1.0
    machine.memes["mystery"] = 0.0
    world.fired.update({("clue_used",), ("mechanism_repaired",), ("friendship_strengthened",)})
    world.say(f"Together, they followed the safe method, and the mechanism clicked into place.")
    world.say(f"{case['ending']}")
    world.say(f"{case['lesson']}. {child.label} and {friend.label} left with dusty hands and a stronger friendship.")

    world.facts.update(case=case, params=params, case_index=_token(params) % len(CASES))
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    p = world.facts["params"]
    return [
        f"Write a child-friendly mystery about {p.child_name} and {p.friend_name} investigating {case['mechanism']}.",
        f"Show how the friends make a cautionary mistake, find evidence, and repair the mechanism together.",
        f"Include a twist revealing whom the warning was protecting, followed by a warm friendship ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    c = world.facts["case"]
    return [
        QAItem(
            f"What were {p.child_name} and {p.friend_name} investigating?",
            f"They were investigating {c['mechanism']} at {p.place}.",
        ),
        QAItem(
            "What warning did they find?",
            f"The warning said, “{c['warning']}”",
        ),
        QAItem(
            "What mistake caused trouble?",
            f"They {c['wrong']}. As a result, {c['setback']}.",
        ),
        QAItem(
            "How did the friends solve the mystery?",
            f"They used the clue and {c['method']}.",
        ),
        QAItem(
            "What was the twist?",
            f"The warning was protecting something: {c['twist']}.",
        ),
        QAItem(
            "How did friendship help?",
            f"They listened to each other, admitted the mistake, and repaired the mechanism by working together.",
        ),
        QAItem(
            "How did the story end?",
            f"{c['ending']} The friends left knowing that {c['lesson'].lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mechanism?", "A mechanism is a group of parts that work together to make something move or perform a job."),
        QAItem("Why should people be careful with warnings?", "Warnings can reveal hidden dangers or protect people, animals, and delicate objects."),
        QAItem("What makes a good friend during a mystery?", "A good friend listens, shares ideas, speaks honestly, and helps solve problems without blaming."),
    ]


ASP_RULES = r"""
mystery(S) :- mechanism(S), clue_found(S).
cautionary_turn(S) :- mystery(S), warning_ignored(S), setback(S).
friendship(S) :- admitted_mistake(S), worked_together(S).
twist(S) :- warning_protected(S).
valid_story(S) :- mystery(S), cautionary_turn(S), friendship(S), twist(S), repaired(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("mechanism", "story1"),
        asp.fact("clue_found", "story1"),
        asp.fact("warning_ignored", "story1"),
        asp.fact("setback", "story1"),
        asp.fact("admitted_mistake", "story1"),
        asp.fact("worked_together", "story1"),
        asp.fact("warning_protected", "story1"),
        asp.fact("repaired", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mechanism friendship cautionary mystery storyworld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", choices=OBJECTS)
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
    friend = args.friend_name or rng.choice([n for n in NAMES if n != name])
    return StoryParams(
        seed=None,
        child_name=name,
        friend_name=friend,
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(child_name="Luna", friend_name="Milo", place="the old clock house", object_name="the brass moon machine"),
    StoryParams(child_name="Iris", friend_name="Theo", place="the lighthouse workshop", object_name="the glass-and-copper mechanism"),
    StoryParams(child_name="Nia", friend_name="Owen", place="the locked garden shed", object_name="the wooden rain wheel"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
