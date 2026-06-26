#!/usr/bin/env python3
"""
A small storyworld for building blocks corner, with Curiosity, Friendship,
and Flashback. The seed premise is a nursery-rhyme-like tale where one child
intends to send a block tower home in triumph, then gloating turns into a
friendship repair and a remembered flashback to how the tower began.
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

SETTING_NAME = "building blocks corner"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str = SETTING_NAME
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    friend: str
    blocker: str
    seed: Optional[int] = None


@dataclass
class Scene:
    id: str
    action: str
    gloat_line: str
    intend_line: str
    send_line: str
    flashback_line: str
    curiosity_hook: str


SCENES = {
    "tower": Scene(
        id="tower",
        action="build a tower",
        gloat_line="Look at my tower so tall!",
        intend_line="I intend to send it up the hall!",
        send_line="send",
        flashback_line="how the first tiny block had been chosen with care",
        curiosity_hook="what would happen if one more blue block went on top",
    ),
    "bridge": Scene(
        id="bridge",
        action="build a bridge",
        gloat_line="Look at my bridge so wide!",
        intend_line="I intend to send it sliding side by side!",
        send_line="send",
        flashback_line="the very first block that made the bridge begin",
        curiosity_hook="whether the bridge could hold a soft stuffed bear",
    ),
    "house": Scene(
        id="house",
        action="build a house",
        gloat_line="Look at my house so neat!",
        intend_line="I intend to send it down the street!",
        send_line="send",
        flashback_line="the first square block and the first careful wall",
        curiosity_hook="which roof block would fit best of all",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben", "Sam"]
FRIEND_NAMES = ["Pip", "June", "Toby", "Milo", "Kit", "Ruby"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: building blocks corner.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--blocker", choices=["tall stack", "leaning arch", "wide bridge"])
    ap.add_argument("--scene", choices=SCENES)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    blocker = args.blocker or rng.choice(["tall stack", "leaning arch", "wide bridge"])
    scene = args.scene or rng.choice(list(SCENES))
    if args.name and args.gender:
        if args.gender == "girl" and args.name not in GIRL_NAMES:
            raise StoryError("That name does not fit the chosen girl story here.")
        if args.gender == "boy" and args.name not in BOY_NAMES:
            raise StoryError("That name does not fit the chosen boy story here.")
    return StoryParams(name=name, gender=gender, friend=friend, blocker=blocker, seed=None)


def tell(params: StoryParams) -> World:
    world = World()
    scene = SCENES[getattr(params, "scene", "tower") if hasattr(params, "scene") else "tower"]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name,
                            traits=["curious", "proud"]))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend,
                              traits=["friendly"]))
    blocks = world.add(Entity(id="blocks", type="toy", label="blocks", phrase="bright wooden blocks",
                              owner=hero.id, meters={"stack": 3.0}, memes={"curiosity": 1.0}))
    obstacle = world.add(Entity(id="obstacle", type="toy", label=params.blocker, phrase=params.blocker))
    world.facts.update(hero=hero, friend=friend, blocks=blocks, obstacle=obstacle, scene=scene)

    world.say(
        f"In the building blocks corner, {hero.id} sat with {hero.pronoun('possessive')} bright blocks, "
        f"where little hands made little plans."
    )
    world.say(
        f"{hero.id} loved to {scene.action}, and {scene.curiosity_hook}; "
        f"that made {hero.pronoun('possessive')} eyes go wide and bright."
    )

    world.para()
    hero.memes["curiosity"] = 1.0
    hero.memes["intend"] = 1.0
    world.say(
        f"{hero.id} looked at the blocks and said, \"{scene.gloat_line}\" "
        f"Then {hero.id} added, \"I {scene.intend_line}\""
    )
    world.say(
        f"But {params.friend} saw the {params.blocker} and gave a tiny frown, "
        f"for the corner was close, and the tower was bound to topple down."
    )

    world.para()
    hero.memes["gloat"] = 1.0
    friend.memes["hurt"] = 1.0
    world.say(
        f"{hero.id} did gloat for a spell, and the boast sounded brave and loud."
    )
    world.say(
        f"Yet {params.friend} said, soft as moss, \"Could I help? Two heads are kinder than one.\""
    )
    world.say(
        f"At that, a flashback fluttered through {hero.id}'s mind: {scene.flashback_line}."
    )
    hero.memes["flashback"] = 1.0
    hero.memes["shame"] = 1.0
    hero.memes["friendship"] = 1.0

    world.para()
    world.say(
        f"{hero.id} stopped the proud parade, and turned the boast to a gentle grin."
    )
    world.say(
        f"\"Yes,\" {hero.id} said, \"let's send the blocks together, and make it strong and true.\""
    )
    world.say(
        f"So {hero.id} and {params.friend} built side by side, one block, then two, then three, "
        f"and the wobbly corner became a merry place."
    )
    world.say(
        f"In the end, the tower stayed up, and the friendship did too, like a ribbon tied in the air."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    return [
        f"Write a short nursery-rhyme story in the building blocks corner about {hero.id}, "
        f"who {scene.action}, then gloat, intend, and finally share the blocks kindly.",
        f"Tell a gentle story where curiosity leads a child to {scene.action}, but friendship changes the ending.",
        f"Write a simple story with the words send, gloat, and intend, set in the building blocks corner.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the blocks?",
            answer=f"{hero.id} wanted to {scene.action} in the building blocks corner.",
        ),
        QAItem(
            question=f"What did {hero.id} say before trying to {scene.send_line} the blocks?",
            answer=f"{hero.id} said, \"{scene.gloat_line}\" and then said, \"I {scene.intend_line}\"",
        ),
        QAItem(
            question=f"Who helped make things better after the boast?",
            answer=f"{friend.id} helped by asking to join in, and that turned the moment into friendship instead of trouble.",
        ),
        QAItem(
            question="What happened when the flashback came?",
            answer=f"{hero.id} remembered {scene.flashback_line}, felt softer inside, and chose to build kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are building blocks?",
            answer="Building blocks are toys children stack, line up, and fit together to make towers, bridges, and little houses.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and help one another play kindly.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a quick look back at something that happened before, like a memory that pops into the mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child may share well when curiosity and friendship are both present.
share(X) :- curious(X), friendly_with(X,Y), goal(X,build), goal(Y,build).

% Gloating can spark hurt feelings; a flashback can soften pride.
hurt(Y) :- gloat(X), heard(Y,X).
soften(X) :- flashback(X), gloat(X).

% Intent to send blocks forward is reasonable only if the structure is stable.
stable(T) :- tower(T), supported(T).
safe_send(X,T) :- intend_send(X,T), stable(T), share(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "building_blocks_corner"))
    lines.append(asp.fact("feature", "curiosity"))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("feature", "flashback"))
    lines.append(asp.fact("can", "send"))
    lines.append(asp.fact("can", "gloat"))
    lines.append(asp.fact("can", "intend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show share/1.\n#show soften/1.\n")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "share")) | set(asp.atoms(model, "soften")))
    if atoms == []:
        print("OK: ASP twin parsed.")
        return 0
    print("OK: ASP twin parsed and produced atoms.")
    return 0


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program("#show share/1.\n#show soften/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", friend="Pip", blocker="tall stack", seed=1),
            StoryParams(name="Leo", gender="boy", friend="June", blocker="leaning arch", seed=2),
            StoryParams(name="Nora", gender="girl", friend="Toby", blocker="wide bridge", seed=3),
        ]
        for p in curated:
            p.scene = "tower"  # type: ignore[attr-defined]
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            if not hasattr(params, "scene"):
                setattr(params, "scene", args.scene or rng.choice(list(SCENES)))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
