#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about an antelope, an onion, hail, and a
friend's backyard.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    friend_name: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Mina", "Lia", "Nora", "Toby", "Milo", "Pip", "Rae", "Sunny"]
FRIENDS = ["Bea", "Ollie", "June", "Finn", "Wren", "Kai"]


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def tell(params: StoryParams) -> World:
    w = World(friend_name=params.friend_name)

    child = w.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    friend = w.add(Entity(id="friend", kind="character", type="child", label=params.friend_name))
    antelope = w.add(Entity(id="antelope", kind="animal", type="antelope", label="antelope"))
    onion = w.add(Entity(id="onion", kind="thing", type="onion", label="onion"))
    hail = w.add(Entity(id="hail", kind="thing", type="hail", label="hail"))

    child.memes["joy"] = 1
    friend.memes["joy"] = 1
    antelope.meters["hops"] = 0
    onion.meters["whole"] = 1
    hail.meters["cold"] = 1

    w.say(f"In a friend's backyard where the berry vines twine, lived {child.id} and {friend.label}.")
    w.say(f"An antelope came with a hop and a shine, to nibble a nibble and make things rhyme.")
    w.para()
    w.say(rhyme_line("The onion was round", "and it sat in the ground"))
    w.say(rhyme_line("The hail came down", "with a ping-ping sound"))

    # Tension: hail frightens the onion patch and starts a little scramble.
    onion.meters["cracked"] = 0
    hail.meters["falling"] = 1
    antelope.meters["startled"] = 1
    child.memes["worry"] = 1

    w.para()
    w.say(
        f"The hail tapped hard on the leaves, and the onion gave a little sigh; "
        f"the antelope blinked at the sky."
    )
    w.say(
        f"{child.id} saw the tiny white pellets and said, 'Oh my! Let's help our friend and not let the garden cry.'"
    )

    # Turn: they make a shelter from a little tray and a blanket.
    w.para()
    shelter = w.add(Entity(id="shelter", kind="thing", type="tray", label="tray", phrase="a little tray"))
    blanket = w.add(Entity(id="blanket", kind="thing", type="blanket", label="blanket", phrase="a soft blanket"))
    shelter.meters["cover"] = 1
    blanket.meters["warmth"] = 1
    antelope.memes["helpful"] = 1
    child.memes["pride"] = 1
    friend.memes["pride"] = 1

    w.say(
        f"{friend.label} held a tray, {child.id} held a blanket, and the antelope stood still as a toy; "
        f"they made a snug little roof with care and with joy."
    )
    w.say(
        f"The onion stayed safe under cover, and the hail bounced off in a bright, tiny shower."
    )

    # Resolution: rhyme ending image.
    w.para()
    onion.meters["cracked"] = 0
    hail.meters["cold"] = 2
    antelope.meters["hops"] = 3
    child.memes["worry"] = 0
    child.memes["joy"] = 2
    friend.memes["joy"] = 2

    w.say(
        f"Then the sun peeped out after the little cold storm, and the backyard felt cozy and warm."
    )
    w.say(
        f"The antelope danced, the onion stood sound, and {child.id} and {friend.label} laughed on the ground."
    )

    w.facts.update(
        child=child,
        friend=friend,
        antelope=antelope,
        onion=onion,
        hail=hail,
        shelter=shelter,
        blanket=blanket,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short nursery rhyme about an antelope, an onion, and hail in a friend's backyard.",
        f"Tell a gentle rhyming story where {f['child'].id} and {f['friend'].label} help the onion when hail begins to fall.",
        "Make the ending cheerful, with a small fix that protects the garden from the hail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].id
    friend = f["friend"].label
    return [
        QAItem(
            question=f"Who was in the backyard with {child}?",
            answer=f"{child} was in the backyard with {friend}, and an antelope joined them too.",
        ),
        QAItem(
            question="What came down from the sky and made the onion worry?",
            answer="Hail came down from the sky and tapped the garden, so the onion looked nervous.",
        ),
        QAItem(
            question="How did they protect the onion?",
            answer="They made a little roof with a tray and a blanket, so the onion stayed safe under cover.",
        ),
        QAItem(
            question="What was the ending image of the story?",
            answer="The hail passed, the antelope danced, and the backyard felt cozy and happy again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hail?",
            answer="Hail is frozen water that falls from clouds as hard little icy bits.",
        ),
        QAItem(
            question="What is an onion?",
            answer="An onion is a round vegetable that grows in the ground and can be used in cooking.",
        ),
        QAItem(
            question="What is a backyard?",
            answer="A backyard is the outdoor space behind a house where children can play and plants can grow.",
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "friend_backyard"),
        asp.fact("contains", "friend_backyard", "antelope"),
        asp.fact("contains", "friend_backyard", "onion"),
        asp.fact("contains", "friend_backyard", "hail"),
        asp.fact("can_hurt", "hail", "onion"),
        asp.fact("can_help", "tray_blanket", "onion"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
unsafe(S) :- contains(S, Obj), can_hurt(H, Obj), contains(S, H).
safe(S) :- setting(S), not unsafe(S).
fix(S) :- safe(S).
fix(S) :- setting(S), contains(S, onion), contains(S, hail).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: antelope, onion, hail.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIENDS)
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice(FRIENDS)
    if name == friend:
        raise StoryError("The child and the friend need different names.")
    return StoryParams(name=name, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
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
    StoryParams(name="Mina", friend_name="Bea"),
    StoryParams(name="Toby", friend_name="June"),
    StoryParams(name="Nora", friend_name="Kai"),
]


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show fix/1.\n#show safe/1.\n")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "fix")))
    if ("friend_backyard",) in atoms:
        print("OK: ASP twin produced a fix for the backyard storyworld.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected fix.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show fix/1.\n#show safe/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show fix/1.\n#show safe/1.\n"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name} and {p.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
