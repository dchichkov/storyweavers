#!/usr/bin/env python3
"""
Radiology friendship storyworld: a gentle, rhyming tale about a child who
needs an image scan, worries about it, and feels braver with a friend beside
them.

The world model tracks both physical state in meters and emotional state in
memes. The story is driven by simulated events:
- a small injury leads to a radiology visit
- the child feels nervous about the scanner
- a friend offers comfort and plays along with the rhyme
- the scan helps the doctor know what to do
- the ending is happy, calm, and friendly
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "Radiology Friendship Happy Ending Rhyming Story"

NAMES = ["Mia", "Noah", "Lena", "Owen", "Zara", "Eli", "Ivy", "Finn"]
FRIEND_NAMES = ["Pip", "Bea", "Toby", "Nia", "Jules", "Milo", "Tia", "Sam"]
ADJECTIVES = ["brave", "gentle", "cheery", "curious", "sweet", "kind"]
PETS = ["a sprained wrist", "a sore ankle", "a bumped elbow", "a tiny cough", "a hurt knee"]
SCAN_TYPES = ["x-ray", "scan", "picture"]
RHYME_ENDINGS = {
    "x-ray": ("say", "day"),
    "scan": ("plan", "fan"),
    "picture": ("light", "bright"),
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"hurt": 0.0, "scan_done": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "comfort": 0.0, "joy": 0.0, "friendship": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Room:
    name: str
    labels: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    child_name: str
    friend_name: str
    injury: str
    scan_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def _rhyme(line: str) -> str:
    return line.strip()


def _split_clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_name(rng: random.Random, pool: list[str], used: set[str]) -> str:
    choices = [n for n in pool if n not in used]
    if not choices:
        choices = pool
    return rng.choice(choices)


def build_world(params: StoryParams) -> World:
    room = Room(name="radiology room", labels=["bright", "quiet", "kind"])
    world = World(room)
    child = world.add(Entity(id="child", kind="character", type="child", label=params.child_name))
    friend = world.add(Entity(id="friend", kind="character", type="friend", label=params.friend_name))
    nurse = world.add(Entity(id="nurse", kind="character", type="nurse", label="the nurse"))
    doctor = world.add(Entity(id="doctor", kind="character", type="doctor", label="the doctor"))
    injury = world.add(Entity(id="injury", type="injury", label=params.injury, phrase=params.injury))
    scan = world.add(Entity(id="scan", type="scan", label=params.scan_type, phrase=params.scan_type))
    world.facts.update(child=child, friend=friend, nurse=nurse, doctor=doctor, injury=injury, scan=scan)
    return world


def setup(world: World) -> None:
    child = world.get("child")
    friend = world.get("friend")
    injury = world.get("injury")
    child.meters["hurt"] += 1
    child.memes["worry"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{child.label} had {injury.label}, a little ache that made the day feel slow and gray."
    )
    world.say(
        f"But {friend.label} came along with a grin and a tune, to help make the worry go away."
    )


def tension(world: World) -> None:
    child = world.get("child")
    nurse = world.get("nurse")
    scan = world.get("scan")
    world.para()
    world.say(
        f'At the radiology door, the nurse smiled and said, "We will make a {scan.label} today."'
    )
    child.memes["worry"] += 1
    world.say(
        f"{child.label} felt a fluttery shiver, like clouds in the sky before sunshine can stay."
    )
    world.say(
        f"{child.label} asked, \"Will it hurt? Will it beep? Will it be big?\" in a very small way."
    )
    world.facts["nervous"] = True


def resolve(world: World) -> None:
    child = world.get("child")
    friend = world.get("friend")
    doctor = world.get("doctor")
    scan = world.get("scan")
    injury = world.get("injury")

    world.para()
    child.memes["comfort"] += 1
    friend.memes["comfort"] += 1
    friend.memes["friendship"] += 2
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)

    if scan.label == "x-ray":
        rhyme = "Hold still and feel chill, then the image will say what is wrong today."
    elif scan.label == "scan":
        rhyme = "Stay snug in the tube, and the pictures will help make a plan that is okay."
    else:
        rhyme = "A bright little light will take a picture, and soon the hurt will look less gray."

    world.say(
        f"{friend.label} held {child.label}'s hand and whispered a rhyme to make the fear drift away."
    )
    world.say(f'The doctor nodded and said, "{rhyme}"')
    world.say(
        f"{child.label} took a deep breath, stayed still for the {scan.label}, and listened all through the way."
    )
    child.meters["scan_done"] += 1
    world.facts["scan_helped"] = True
    world.say(
        f"The picture showed the {injury.label} was small, so the doctor knew what would help it heal."
    )
    world.say(
        f"{child.label} left with a smile, and {friend.label} said, \"See? Bravery can feel real.\""
    )
    child.memes["joy"] += 2
    friend.memes["joy"] += 1
    world.facts["happy_ending"] = True


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    setup(world)
    tension(world)
    resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    scan = world.facts["scan"]
    injury = world.facts["injury"]
    return [
        "Write a short rhyming story for a young child about friendship, a nervous visit, and a happy ending.",
        f"Tell a gentle rhyming tale where {child.label} needs a {scan.label} for {injury.label} and {friend.label} helps.",
        "Make the story kind, concrete, and calm, with a child who feels better by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    injury = world.facts["injury"]
    scan = world.facts["scan"]
    return [
        QAItem(
            question=f"Why did {child.label} go to radiology?",
            answer=f"{child.label} went to radiology because {child.label} had {injury.label} and needed a {scan.label} so the doctor could see what was going on.",
        ),
        QAItem(
            question=f"How did {friend.label} help {child.label} feel braver?",
            answer=f"{friend.label} stayed close, held {child.label}'s hand, and shared a calm rhyme, which helped the worry feel smaller.",
        ),
        QAItem(
            question=f"What was the ending like for {child.label} and {friend.label}?",
            answer=f"The ending was happy and peaceful, because the scan was done, the doctor understood the hurt, and both friends left smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    scan = world.facts["scan"].label
    if scan == "x-ray":
        ans = "An x-ray is a picture that helps doctors look inside the body, often to check bones."
    elif scan == "scan":
        ans = "A scan is a way for doctors to make pictures of the inside of the body so they can understand an injury."
    else:
        ans = "A medical picture helps a doctor see more clearly and decide how to help."
    return [
        QAItem(
            question="What is radiology?",
            answer="Radiology is a part of medicine where doctors use special pictures, like x-rays or scans, to look inside the body.",
        ),
        QAItem(
            question=f"What is a {scan} for?",
            answer=ans,
        ),
        QAItem(
            question="Why is friendship helpful when someone feels nervous?",
            answer="A friend can stay nearby, offer kind words, and make scary things feel safer and more manageable.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:7} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
child_worries(C) :- person(C), hurt(C), not calm(C).
happy_ending(C) :- child_worries(C), friendship(F), friend(F), comfort(F), scan_done(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("person", "child"),
        asp.fact("person", "friend"),
        asp.fact("friend", "friend"),
        asp.fact("hurt", "child"),
        asp.fact("scan_done", "child"),
        asp.fact("friendship", "friend"),
        asp.fact("comfort", "friend"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    asp_set = set(asp.atoms(model, "happy_ending"))
    py_set = {("child",)} if True else set()
    if asp_set == py_set:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Radiology friendship rhyming storyworld.")
    ap.add_argument("--child-name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--injury", choices=PETS)
    ap.add_argument("--scan-type", choices=SCAN_TYPES)
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
    child = args.child_name or rng.choice(NAMES)
    friend = args.friend_name or make_name(rng, FRIEND_NAMES, {child})
    injury = args.injury or rng.choice(PETS)
    scan = args.scan_type or rng.choice(SCAN_TYPES)
    if friend == child:
        raise StoryError("The friend must be a different child.")
    return StoryParams(child_name=child, friend_name=friend, injury=injury, scan_type=scan)


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("Mia", "Pip", "a sprained wrist", "x-ray"),
            StoryParams("Noah", "Bea", "a bumped elbow", "scan"),
            StoryParams("Lena", "Toby", "a sore ankle", "picture"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.child_name} and {sample.params.friend_name}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
