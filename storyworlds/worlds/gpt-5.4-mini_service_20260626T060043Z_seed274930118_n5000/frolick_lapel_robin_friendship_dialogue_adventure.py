#!/usr/bin/env python3
"""
storyworlds/worlds/frolick_lapel_robin_friendship_dialogue_adventure.py
=======================================================================

A small adventure storyworld about a child, a friendly robin, and a windy little
quest. The seed words are woven into the model: frolick, lapel, robin.

Premise:
- A child and a robin friend set out on a cheerful adventure.
- They frolick through a garden path to find a lost token for a waiting friend.

Tension:
- The wind tugs at the child's coat lapel and starts to scatter the trail.
- The child worries the adventure will fail.

Turn:
- The robin notices a clue from above and speaks up in simple dialogue.
- Friendship turns the moment from worry into teamwork.

Resolution:
- They follow the robin's hint, recover the missing token, and end with a warm
  image of companionship and a safe, happy return.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "robin":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the garden path"
    bright: bool = True
    outdoors: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", bright=True, outdoors=True),
    "orchard": Setting(place="the orchard", bright=True, outdoors=True),
    "meadow": Setting(place="the meadow", bright=True, outdoors=True),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lina", "Pia", "Sage"],
    "boy": ["Theo", "Finn", "Eli", "Milo", "Otto"],
}

FRIENDS = {
    "robin": {
        "label": "a robin friend",
        "type": "robin",
        "phrase": "a quick little robin with bright eyes",
    }
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid adventure needs an outdoor place and a robin companion.
valid_story(Place, Friend) :- place(Place), outdoors(Place), friend(Friend), robin(Friend).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.outdoors:
            lines.append(asp.fact("outdoors", place))
        if setting.bright:
            lines.append(asp.fact("bright", place))
    for fid, _ in FRIENDS.items():
        lines.append(asp.fact("friend", fid))
        lines.append(asp.fact("robin", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, "robin") for p in SETTINGS if SETTINGS[p].outdoors}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"tired": 0.0, "joy": 0.0, "worry": 0.0, "courage": 0.0},
        memes={"friendship": 1.0, "curiosity": 1.0, "trust": 1.0},
    ))
    robin = world.add(Entity(
        id="robin",
        kind="character",
        type="robin",
        label="the robin",
        phrase=FRIENDS["robin"]["phrase"],
        meters={"air": 1.0, "help": 0.0},
        memes={"friendship": 1.0, "alertness": 1.0},
    ))
    lapel = world.add(Entity(
        id="lapel",
        kind="thing",
        type="lapel",
        label="lapel",
        phrase="a bright brass lapel pin",
        owner=hero.id,
        worn_by=hero.id,
        meters={"shine": 1.0, "looseness": 0.0},
    ))
    token = world.add(Entity(
        id="token",
        kind="thing",
        type="token",
        label="token",
        phrase="a little silver token for a friend",
        owner="friend",
        meters={"lost": 1.0, "found": 0.0},
    ))
    world.facts.update(hero=hero, robin=robin, lapel=lapel, token=token, params=params)
    return world


def intro(world: World) -> None:
    h: Entity = world.facts["hero"]  # type: ignore[assignment]
    r: Entity = world.facts["robin"]  # type: ignore[assignment]
    world.say(
        f"{h.id} was a curious little {h.type} who loved an adventure, especially when it was gentle enough to frolick along the path."
    )
    world.say(
        f"On the branch above, {r.phrase} waited like a tiny guide."
    )
    world.say(
        f"{h.id} trusted the robin, and the robin seemed to trust {h.pronoun('object')} right back."
    )


def journey(world: World) -> None:
    h: Entity = world.facts["hero"]  # type: ignore[assignment]
    r: Entity = world.facts["robin"]  # type: ignore[assignment]
    t: Entity = world.facts["token"]  # type: ignore[assignment]
    l: Entity = world.facts["lapel"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"One bright morning, {h.id} and the robin set out through {world.setting.place}."
    )
    world.say(
        f"They frolicked beside the hedges, looking for the little token that had gone missing."
    )
    world.say(
        f"{h.id} said, \"Do you see it?\" and the robin answered, \"Cheep! Not yet, but we can keep going.\""
    )
    h.meters["joy"] += 1
    h.memes["friendship"] += 1
    r.meters["help"] += 1
    t.meters["lost"] += 0.2
    l.meters["shine"] += 0.1


def tension(world: World) -> None:
    h: Entity = world.facts["hero"]  # type: ignore[assignment]
    r: Entity = world.facts["robin"]  # type: ignore[assignment]
    l: Entity = world.facts["lapel"]  # type: ignore[assignment]
    t: Entity = world.facts["token"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"Then the wind tugged at {h.pronoun('possessive')} coat lapel and made the little pin wobble."
    )
    l.meters["looseness"] += 1.0
    h.meters["worry"] += 1.0
    h.meters["courage"] += 0.5
    world.say(
        f"{h.id} frowned. \"Oh no,\" {h.pronoun()} said, \"I might drop the lapel pin before we find the token.\""
    )
    world.say(
        f"The robin hopped close and said, \"Stay with me. Friendship makes a windy day feel smaller.\""
    )
    t.meters["lost"] += 0.3
    r.memes["friendship"] += 0.5


def turn_and_resolution(world: World) -> None:
    h: Entity = world.facts["hero"]  # type: ignore[assignment]
    r: Entity = world.facts["robin"]  # type: ignore[assignment]
    t: Entity = world.facts["token"]  # type: ignore[assignment]
    l: Entity = world.facts["lapel"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"The robin flew up high and called, \"There! Under the blue bush!\""
    )
    world.say(
        f"{h.id} looked where the robin pointed and spotted the silver token shining in the grass."
    )
    t.meters["found"] = 1.0
    t.meters["lost"] = 0.0
    h.meters["worry"] = 0.0
    h.meters["joy"] += 1.5
    h.memes["friendship"] += 1.0
    r.meters["help"] += 1.0
    l.meters["looseness"] = 0.0
    world.say(
        f"{h.id} tucked the lapel pin snug again, then smiled as {h.id} picked up the token."
    )
    world.say(
        f"\"We did it together,\" {h.id} said. The robin chirped, and the two friends went home side by side, still feeling like the best kind of adventure team."
    )


def tell_story(world: World) -> None:
    intro(world)
    journey(world)
    tension(world)
    turn_and_resolution(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a short adventure story for a young child about {p.name} and a robin who go frolicking in {p.place}.",
        f"Tell a friendly dialogue-heavy tale where a child and a robin search for a lost token and mention the word lapel.",
        f"Write a gentle outdoor adventure about friendship, a windy lapel, and a robin who helps find the missing thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    h: Entity = world.facts["hero"]  # type: ignore[assignment]
    t: Entity = world.facts["token"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who went on the adventure in {p.place}?",
            answer=f"{p.name} went on the adventure with a robin friend in {p.place}. They stayed together the whole time.",
        ),
        QAItem(
            question="What did the friends do while they looked for the lost token?",
            answer=f"They frolicked along the path, kept talking to each other, and searched carefully until they found it.",
        ),
        QAItem(
            question="Why did the child worry about the coat lapel?",
            answer=f"{p.name} worried because the wind made the lapel pin wobble, and that felt like it might spoil the adventure for a moment.",
        ),
        QAItem(
            question="How did the robin help in the middle of the story?",
            answer="The robin flew up high, spotted the token from above, and called out the place where it was hiding.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The token was found, the lapel pin was tucked safely again, and {p.name} felt happy and brave with the robin beside them.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a robin?",
        answer="A robin is a small bird with a lively hop and a clear voice. It often moves quickly and notices tiny things on the ground.",
    ),
    QAItem(
        question="What is a lapel?",
        answer="A lapel is the folded front edge of a coat or jacket. A pin can be attached to it so it stays neat and looks nice.",
    ),
    QAItem(
        question="What does it mean to frolick?",
        answer="To frolick means to play in a lively, joyful way, often with quick little movements and happy energy.",
    ),
    QAItem(
        question="What is friendship?",
        answer="Friendship is the caring bond between people or creatures who help each other, share time together, and feel happy together.",
    ),
    QAItem(
        question="Why can dialogue make a story feel adventurous?",
        answer="Dialogue lets the characters speak to each other, so their plans, worries, and brave ideas feel alive while the adventure moves forward.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasoning / parameter resolution
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [(place, "robin") for place, setting in SETTINGS.items() if setting.outdoors]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: frolick, lapel, robin.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(sorted(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, name=name, gender=gender, friend="robin")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def asp_verify_main() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify_main())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combinations:\n")
        for place, friend in stories:
            print(f"  {place:10} {friend}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in sorted(SETTINGS):
            params = StoryParams(place=place, name=NAMES["girl"][0], gender="girl", friend="robin")
            samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
