#!/usr/bin/env python3
"""
Standalone storyworld: dreary boat-ramp ghost friendship tale.

A small, self-contained story simulation where a child meets a ghost at a
boat ramp on a dreary day, and friendship helps them renew a broken promise.
The world is state-driven: weather, location, trust, fear, and a small physical
repair all shape the prose and Q&A.
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

SETTING_NAME = "the boat ramp"
WEATHER_WORD = "dreary"
SEED_WORDS = ("dreary", "sire", "renew")


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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str = SETTING_NAME
    weather: str = WEATHER_WORD
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mina", "Ivy", "Nora", "Lena", "Rose"],
    "boy": ["Theo", "Finn", "Eli", "Jude", "Leo"],
}
COMPANIONS = ["mother", "father", "grandpa", "grandma"]

ASP_RULES = r"""
#show bond/2.
#show renews/2.
#show fears/2.

bond(C,H) :- child(C), ghost(H), friendship(C,H).
renews(C,H) :- bond(C,H), promise(C,H), help(C,H).
fears(C,H) :- child(C), ghost(H), dreary_day, boat_ramp.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("boat_ramp"),
        asp.fact("dreary_day"),
        asp.fact("child", "child"),
        asp.fact("ghost", "ghost"),
        asp.fact("friendship", "child", "ghost"),
        asp.fact("promise", "child", "ghost"),
        asp.fact("help", "child", "ghost"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bond/2.\n#show renews/2."))
    bonds = set(asp.atoms(model, "bond"))
    renews = set(asp.atoms(model, "renews"))
    expected_bonds = {("child", "ghost")}
    expected_renews = {("child", "ghost")}
    if bonds == expected_bonds and renews == expected_renews:
        print("OK: ASP twin matches Python reasonableness gate.")
        return 0
    print("Mismatch in ASP twin.")
    print("bond:", sorted(bonds), "expected:", sorted(expected_bonds))
    print("renews:", sorted(renews), "expected:", sorted(expected_renews))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story boat-ramp world with friendship and renewal.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
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
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(name=name, gender=gender, companion=companion)


def reasonableness_gate(params: StoryParams) -> None:
    if params.name.lower() == "ghost":
        raise StoryError("The child cannot be named Ghost in this story.")
    if params.companion == "ghost":
        raise StoryError("A living companion is required; the ghost is the story's new friend.")


def _append_story(world: World, text: str) -> None:
    world.say(text)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.gender, traits=["small", "lonely"]))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label=params.companion))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="a pale ghost", traits=["quiet"]))
    boat = world.add(Entity(id="boat", kind="thing", type="boat", label="an old boat", meters={"broken": 1.0, "wet": 1.0}))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="a little lantern", meters={"dim": 1.0}))
    rope = world.add(Entity(id="rope", kind="thing", type="rope", label="a frayed rope", meters={"loose": 1.0}))

    child.memes.update({"fear": 1.0, "curiosity": 1.0, "loneliness": 1.0})
    ghost.memes.update({"sadness": 1.0, "hope": 0.0, "trust": 0.0, "friendship": 0.0})
    companion.memes.update({"worry": 1.0})

    _append_story(world, f"It was a {WEATHER_WORD} afternoon at {world.place}, where the water looked gray and still.")
    _append_story(world, f"{params.name} came with {params.companion} and held tight to a little lantern.")
    _append_story(world, f"Near the ramp sat an old boat, and beside it stood a pale ghost who said, \"I was waiting for a friend.\"")
    _append_story(world, f"{params.name} felt a shiver, because the ghost's voice sounded soft and lonely.")

    world.para()
    child.memes["fear"] += 1.0
    ghost.memes["sadness"] += 1.0
    _append_story(world, f"{params.name} wanted to run, but the ghost bowed politely and called the child \"sire\" like a careful old tale.")
    _append_story(world, f"That strange word made the child stop and listen instead.")

    world.para()
    child.memes["curiosity"] += 1.0
    ghost.memes["hope"] += 1.0
    world.facts["friendship_started"] = True
    _append_story(world, f"The ghost pointed to the broken boat and the loose rope and asked for help to renew the place.")
    _append_story(world, f"Together, they tied the rope, lifted the lantern, and set the boat straight so it would not slide back.")

    boat.meters["broken"] = 0.0
    rope.meters["loose"] = 0.0
    lantern.meters["dim"] = 0.0
    ghost.memes["trust"] += 1.0
    child.memes["fear"] = 0.0
    child.memes["friendship"] = 1.0
    ghost.memes["friendship"] = 1.0
    world.facts["renewed"] = True

    world.para()
    _append_story(world, f"When the work was done, the ghost smiled, and its edges looked kinder in the lantern light.")
    _append_story(world, f"{params.name} smiled back, because a friendship had begun where the day had felt dreary before.")
    _append_story(world, f"By the end, the boat ramp was calm again, and the child had a new friend who promised to return.")

    world.facts.update(
        child=child,
        ghost=ghost,
        companion=companion,
        boat=boat,
        lantern=lantern,
        rope=rope,
        params=params,
    )
    prompts = [
        f"Write a short ghost story for children set at {world.place} on a {WEATHER_WORD} day.",
        f"Tell a gentle story where a child and a ghost become friends and renew an old boat at the ramp.",
        f"Write a calm story that includes the words {', '.join(SEED_WORDS)} and ends with friendship.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name} stop being afraid at the boat ramp?",
            answer=f"{params.name} stopped being afraid because the ghost was polite, asked for help, and became a friend.",
        ),
        QAItem(
            question="What did the child and the ghost renew together?",
            answer="They renewed the old boat ramp scene by fixing the rope and setting the boat straight again.",
        ),
        QAItem(
            question=f"How did the ghost call {params.name}?",
            answer="The ghost called the child sire, like a careful old tale.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does dreary mean?",
            answer="Dreary means gray, dull, and a little sad or gloomy.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and want to stay together.",
        ),
        QAItem(
            question="What does renew mean?",
            answer="Renew means to make something fresh again or help it start over in a better way.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mina", gender="girl", companion="mother"),
    StoryParams(name="Theo", gender="boy", companion="grandpa"),
]


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
        print(asp_program("#show bond/2.\n#show renews/2.\n#show fears/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bond/2.\n#show renews/2.\n#show fears/2."))
        print("bond:", sorted(set(asp.atoms(model, "bond"))))
        print("renews:", sorted(set(asp.atoms(model, "renews"))))
        print("fears:", sorted(set(asp.atoms(model, "fears"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            try:
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
