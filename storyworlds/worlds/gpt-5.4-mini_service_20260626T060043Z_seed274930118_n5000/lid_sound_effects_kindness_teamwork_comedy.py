#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lid_sound_effects_kindness_teamwork_comedy.py
===============================================================================================================

A standalone story world for a tiny comedy about a stuck lid, kind helping,
and teamwork that makes a silly sound-filled fix.

Seed tale:
- A child wants to open a jar or box with a stubborn lid.
- The lid makes a comedic battle of sounds: pop, tap, squeak, thunk.
- A helper offers kindness instead of teasing.
- Two or more characters team up, share a method, and finally free the lid.
- The ending proves the change: snack shared, lid open, nobody grumpy.

This world intentionally keeps the domain small:
one place, one problem, one cooperative solution, one cheerful ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% A lid is stuck if the container is closed and the opener is not enough.
stuck(C) :- container(C), closed(C), needs_teamwork(C).

% A container has a fix when a helper is kind and teamwork is available.
fix(C) :- container(C), kind_helper(H), teamwork(H, C).

% A valid story requires a stuck lid, a fix, and a comedic sound sequence.
valid_story(Setting, Container, Tone) :- place(Setting), stuck(Container), fix(Container), tone(Tone).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"closed": 0.0, "stuck": 0.0, "open": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "teamwork": 0.0, "joy": 0.0, "frustration": 0.0}


@dataclass
class Setting:
    place: str
    tone: str = "comedy"


@dataclass
class ContainerSpec:
    label: str
    phrase: str
    lid_name: str
    sound_start: str
    sound_middle: str
    sound_end: str
    needs_two_hands: bool = True


@dataclass
class StoryParams:
    place: str
    container: str
    name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "kitchen": Setting(place="the kitchen"),
    "picnic": Setting(place="the picnic blanket"),
    "pantry": Setting(place="the pantry"),
}

CONTAINERS = {
    "jar": ContainerSpec(
        label="jar",
        phrase="a glass jar of cookies",
        lid_name="lid",
        sound_start="tap-tap",
        sound_middle="squeeeak",
        sound_end="POP!",
    ),
    "box": ContainerSpec(
        label="box",
        phrase="a treat box with a snug lid",
        lid_name="lid",
        sound_start="thunk-thunk",
        sound_middle="scrrritch",
        sound_end="plip!",
    ),
    "tin": ContainerSpec(
        label="tin",
        phrase="a shiny tin of crackers",
        lid_name="lid",
        sound_start="clink-clink",
        sound_middle="rrrmmph",
        sound_end="POOF!",
    ),
}

NAMES = ["Mia", "Noah", "Lila", "Finn", "Ava", "Leo", "Zoe", "Max"]
HELPERS = ["Aunt June", "Dad", "Mom", "Grandpa", "Big Sis"]
TONE_WORDS = ["comedy", "silly", "playful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, container) for place in SETTINGS for container in CONTAINERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny comedy world about a stuck lid, kind help, and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.container:
        combos = [c for c in combos if c[1] == args.container]
    if not combos:
        raise StoryError("No valid combination matches the chosen options.")

    place, container = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPERS if n != name])
    return StoryParams(place=place, container=container, name=name, helper_name=helper_name)


def _sound_line(spec: ContainerSpec, stage: int) -> str:
    return [spec.sound_start, spec.sound_middle, spec.sound_end][stage]


def tell(setting: Setting, spec: ContainerSpec, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", label=child_name, type="child"))
    helper = world.add(Entity(id=helper_name, kind="character", label=helper_name, type="helper"))
    lid = world.add(Entity(id="lid", kind="thing", label=spec.lid_name, type="lid"))
    container = world.add(Entity(id="container", kind="thing", label=spec.label, type=spec.label))

    world.facts.update(setting=setting, spec=spec, child=child, helper=helper, lid=lid, container=container)

    # Beginning
    world.say(f"{child_name} found {spec.phrase} at {setting.place}.")
    world.say(f"Right on top was a {spec.lid_name} that looked brave, stubborn, and just a little bit smug.")
    world.say(f"{child_name} gave it a try. {child_name} twisted and tugged. { _sound_line(spec, 0) }")
    child.memes["frustration"] += 1
    lid.meters["closed"] = 1.0
    lid.meters["stuck"] = 1.0

    # Middle
    world.say(f"{child_name} leaned harder. { _sound_line(spec, 1) }")
    world.say(f"The {spec.lid_name} did not budge, which was rude for a tiny piece of metal.")
    helper.memes["kindness"] += 1
    world.say(f"{helper_name} came over and said, \"Need a hand?\"")
    world.say(f"{child_name} nodded, because the lid was winning and that was embarrassing.")

    # Teamwork turn
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(f"They counted together: one, two, three!")
    world.say(f"{helper_name} held the jar steady while {child_name} twisted again. { _sound_line(spec, 2) }")
    world.say("The lid popped free so fast that everyone blinked at it.")

    # Resolution
    lid.meters["open"] = 1.0
    lid.meters["closed"] = 0.0
    lid.meters["stuck"] = 0.0
    child.memes["joy"] += 2
    helper.memes["joy"] += 1
    world.say(f"{child_name} laughed, because the big victory came from a very small lid.")
    world.say(f"Then they shared the snacks, and the once-stuck {spec.label} sat open and proud on the table.")
    world.say(f"The whole room felt happier, and the only thing still tight was everybody's smile.")

    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CONTAINERS[params.container], params.name, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    spec: ContainerSpec = f["spec"]
    return [
        f'Write a short funny story for a young child about a stubborn {spec.lid_name} that finally opens with help.',
        f"Tell a comedy story where {f['child'].id} and {f['helper'].id} use kindness and teamwork to open {spec.phrase}.",
        f"Write a playful story full of sound effects like {spec.sound_start}, {spec.sound_middle}, and {spec.sound_end}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    spec: ContainerSpec = f["spec"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What was {child.id} trying to open at {setting.place}?",
            answer=f"{child.id} was trying to open {spec.phrase} with a stubborn {spec.lid_name}.",
        ),
        QAItem(
            question=f"Who helped {child.id} with the {spec.lid_name}?",
            answer=f"{helper.id} helped by holding the container steady and working together with {child.id}.",
        ),
        QAItem(
            question=f"What sound happened when the {spec.lid_name} finally came off?",
            answer=f"It went {spec.sound_end}, and then everyone laughed because the little battle was over.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and relieved, because kindness and teamwork turned the stuck lid into an open snack.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lid?",
            answer="A lid is a cover that sits on top of something like a jar, tin, or box to keep it closed.",
        ),
        QAItem(
            question="Why do people use kindness when something is hard?",
            answer="Kindness helps people stay calm, feel supported, and work together instead of getting cranky.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when two or more people help with the same job and each person does a part.",
        ),
        QAItem(
            question="Why can funny sound effects make a story feel like comedy?",
            answer="Funny sound effects make the action feel bouncy and lively, so the scene sounds silly instead of serious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for cid, spec in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if spec.needs_two_hands:
            lines.append(asp.fact("needs_teamwork", cid))
        lines.append(asp.fact("tone", "comedy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((a, b) for (a, b, *_rest) in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(place="kitchen", container="jar", name="Mia", helper_name="Dad"),
    StoryParams(place="picnic", container="box", name="Leo", helper_name="Aunt June"),
    StoryParams(place="pantry", container="tin", name="Zoe", helper_name="Mom"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n * 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.container} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
