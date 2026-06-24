#!/usr/bin/env python3
"""
A small story world about animal friends, a piece of technology, sharing, and
a misunderstanding that gets fixed with a kind conversation.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    borrowed_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"dog", "puppy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"bird"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Friend:
    name: str
    type: str
    trait: str
    pronoun_set: str


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    use: str
    shared_use: str
    signal: str
    shape: str


@dataclass
class StoryParams:
    name_a: str
    animal_a: str
    trait_a: str
    name_b: str
    animal_b: str
    trait_b: str
    device: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


FRIEND_TRAITS = ["curious", "gentle", "playful", "shy", "cheerful", "thoughtful"]
ANIMALS = ["cat", "dog", "rabbit", "fox", "bear", "otter", "mouse", "panda", "bird"]
SETTINGS = {
    "treehouse": "the treehouse",
    "garden": "the garden",
    "playroom": "the playroom",
    "porch": "the porch",
}
DEVICES = {
    "tablet": Device(
        id="tablet",
        label="tablet",
        phrase="a shiny tablet",
        use="draw pictures on the tablet",
        shared_use="take turns drawing on the tablet",
        signal="screen",
        shape="small",
    ),
    "camera": Device(
        id="camera",
        label="camera",
        phrase="a little camera with a bright button",
        use="take photos with the camera",
        shared_use="look at the photos together",
        signal="flash",
        shape="boxy",
    ),
    "radio": Device(
        id="radio",
        label="radio",
        phrase="a tiny radio with a soft dial",
        use="listen to songs on the radio",
        shared_use="share the radio and listen one at a time",
        signal="music",
        shape="round",
    ),
    "gamepad": Device(
        id="gamepad",
        label="gamepad",
        phrase="a gamepad with colorful buttons",
        use="play a simple game on the gamepad",
        shared_use="pass the gamepad back and forth",
        signal="beeps",
        shape="flat",
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for dev in DEVICES:
            combos.append((setting, dev))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about sharing technology after a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--name-a")
    ap.add_argument("--animal-a", choices=ANIMALS)
    ap.add_argument("--trait-a", choices=FRIEND_TRAITS)
    ap.add_argument("--name-b")
    ap.add_argument("--animal-b", choices=ANIMALS)
    ap.add_argument("--trait-b", choices=FRIEND_TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    device = args.device or rng.choice(list(DEVICES))
    a_animal = args.animal_a or rng.choice(ANIMALS)
    b_animal = args.animal_b or rng.choice([x for x in ANIMALS if x != a_animal])
    a_trait = args.trait_a or rng.choice(FRIEND_TRAITS)
    b_trait = args.trait_b or rng.choice([x for x in FRIEND_TRAITS if x != a_trait])
    name_a = args.name_a or rng.choice(["Milo", "Luna", "Pip", "Nina", "Toby", "Kiki", "Ollie"])
    name_b = args.name_b or rng.choice(["Mina", "Jasper", "Nori", "Penny", "Momo", "Ravi", "Bean"])
    return StoryParams(
        name_a=name_a,
        animal_a=a_animal,
        trait_a=a_trait,
        name_b=name_b,
        animal_b=b_animal,
        trait_b=b_trait,
        device=device,
        setting=setting,
    )


def _friend_label(name: str, animal: str, trait: str) -> str:
    return f"{trait} {animal} {name}"


def _do_misunderstanding(world: World, a: Entity, b: Entity, dev: Device) -> None:
    a.memes["worry"] = 1
    b.memes["sad"] = 1
    world.say(f"{a.id} thought {b.id} was keeping the {dev.label} all to {b.pronoun('possessive')}self.")
    world.say(f"{b.id} felt left out because {a.id} had turned away with a puzzled look.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    a = world.add(Entity(id=params.name_a, kind="character", type=params.animal_a, label=params.name_a))
    b = world.add(Entity(id=params.name_b, kind="character", type=params.animal_b, label=params.name_b))
    dev = DEVICES[params.device]
    device = world.add(Entity(id=dev.id, type="technology", label=dev.label, phrase=dev.phrase, owner=a.id))
    device.borrowed_by = None

    world.say(
        f"In {world.setting}, {params.name_a} was a {params.trait_a} {params.animal_a} and "
        f"{params.name_b} was a {params.trait_b} {params.animal_b}."
    )
    world.say(
        f"They loved the little {dev.label}, because it let them {dev.use}."
    )
    world.para()
    world.say(
        f"One afternoon, {params.name_a} carried {device.phrase} outside and started to use it."
    )
    world.say(
        f"{params.name_b} came close and reached for it too, hoping to {dev.shared_use}."
    )
    _do_misunderstanding(world, a, b, dev)
    world.para()
    world.say(
        f"{params.name_a} noticed the sad face and stopped."
    )
    world.say(
        f'"Oh! I did not mean to keep it away," {params.name_a} said. "I was just waiting for the battery light to stop blinking."'
    )
    world.say(
        f'{params.name_b} blinked, then smiled. "I thought you were saying no," {params.name_b} said.'
    )
    world.say(
        f'Then they decided to {dev.shared_use}, and the little {dev.label} felt even more fun when both friends used it together.'
    )
    world.para()
    a.memes["joy"] = 1
    b.memes["joy"] = 1
    a.memes["worry"] = 0
    b.memes["sad"] = 0
    device.borrowed_by = b.id
    world.facts.update(friend_a=a, friend_b=b, device=device, dev=dev, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    dev = world.facts["dev"]
    return [
        f"Write a short animal story about sharing {dev.label} and fixing a misunderstanding.",
        f"Tell a gentle story where {p.name_a} and {p.name_b} both want to use {dev.phrase}.",
        f"Write a child-friendly story with animals, a {dev.label}, and a kind apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    dev = world.facts["dev"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The friends were {p.name_a}, a {p.trait_a} {p.animal_a}, and {p.name_b}, a {p.trait_b} {p.animal_b}.",
        ),
        QAItem(
            question=f"What technology did they want to share?",
            answer=f"They wanted to share {dev.phrase}. It was the little {dev.label} that helped them {dev.use}.",
        ),
        QAItem(
            question=f"Why did the friends have a misunderstanding?",
            answer=(
                f"{p.name_a} thought {p.name_b} was keeping the {dev.label} for {p.name_b} alone, "
                f"and {p.name_b} thought {p.name_a} was saying no. They were both mistaken."
            ),
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They talked kindly, explained the blinking battery light, and chose to {dev.shared_use}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    dev = world.facts["dev"]
    return [
        QAItem(
            question="What is technology?",
            answer="Technology is a tool or machine people use to do things, like draw, listen, take pictures, or play games.",
        ),
        QAItem(
            question=f"Why do friends take turns with something like a {dev.label}?",
            answer="Taking turns helps everyone share fairly so each friend gets a chance to use the thing and nobody feels left out.",
        ),
        QAItem(
            question="What should you do when you misunderstand a friend?",
            answer="You should ask a question, listen carefully, and say sorry if you were wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} owner={e.owner} borrowed_by={e.borrowed_by} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
setting(treehouse). setting(garden). setting(playroom). setting(porch).
device(tablet). device(camera). device(radio). device(gamepad).
valid(S,D) :- setting(S), device(D).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("setting", s) for s in SETTINGS] + [asp.fact("device", d) for d in DEVICES])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(python_set - clingo_set))
    print(" only in clingo:", sorted(clingo_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("Milo", "cat", "curious", "Pip", "rabbit", "gentle", "tablet", "garden"),
    StoryParams("Luna", "dog", "playful", "Nori", "fox", "thoughtful", "camera", "treehouse"),
    StoryParams("Kiki", "bird", "cheerful", "Bean", "mouse", "shy", "radio", "porch"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for s, d in combos:
            print(f"  {s} {d}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
            header = f"### {p.name_a} and {p.name_b} at {p.setting} with {p.device}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
